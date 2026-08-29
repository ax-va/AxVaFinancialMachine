import base64
import functools
import json
import logging

import httpx

from finanzmaschine_staking.sync_clients.decorators import retry, rate_limit
from finanzmaschine_staking.sync_clients.near.rpc_client_exeptions import BlockHeightNotFoundError

logger = logging.getLogger(__name__)


def handle_block_height_not_found(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 422:
                raise

            data = exc.response.json()
            error = data.get("error", {})
            cause = error.get("cause", {})

            if cause.get("name") != "UNKNOWN_BLOCK":
                raise

            block_height = (
                cause
                .get("info", {})
                .get("block_reference", {})
                .get("block_id")
            )

            raise BlockHeightNotFoundError(
                f"Block height {block_height} not found"
            ) from exc

    return wrapper


class RpcClient:
    REGULAR_URL = "https://rpc.mainnet.fastnear.com"
    ARCHIVAL_URL = "https://archival-rpc.mainnet.fastnear.com"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    @retry(
        max_retries=5,
        min_retry_delay_sec=5.0,
        exceptions=httpx.HTTPStatusError,
    )
    @rate_limit(min_interval_sec=2.0)
    @handle_block_height_not_found
    def call_view_function(
        self,
        contract_id: str,
        method_name: str,
        args: dict,
        block_height: int,
    ) -> bytes:
        """
        Calls a NEAR smart contract view function at a given block height.
        The call is read-only and does not create a transaction or modify blockchain state.

        Args:
            contract_id: NEAR account ID of the smart contract.
            method_name: Name of the view function to call.
            args: Arguments passed to the contract function.
            block_height: Block height at which to query the contract state.

        Returns:
            Raw bytes returned by the view function.

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails.
            RuntimeError: If the NEAR RPC returns an error.
        """
        args_base64 = base64.b64encode(
            json.dumps(args).encode()
        ).decode()

        payload = {
            "jsonrpc": "2.0",
            "id": "staking",
            "method": "query",
            "params": {
                "request_type": "call_function",
                "account_id": contract_id,
                "method_name": method_name,
                "args_base64": args_base64,
                "block_id": block_height,
                }
        }

        response = self._client.post(
            self.ARCHIVAL_URL,
            json=payload,
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"NEAR RPC error: {data['error']}"
            )

        result = data["result"]["result"]

        return bytes(result)

    @retry(
        max_retries=5,
        min_retry_delay_sec=5.0,
        exceptions=httpx.HTTPStatusError,
    )
    @rate_limit(min_interval_sec=2.0)
    def get_final_block_height(self) -> int:
        payload = {
            "jsonrpc": "2.0",
            "id": "staking",
            "method": "block",
            "params": {
                "finality": "final",
                }
        }

        response = self._client.post(
            self.REGULAR_URL,
            json=payload,
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"NEAR RPC error: {data['error']}"
            )

        return data["result"]["header"]["height"]
