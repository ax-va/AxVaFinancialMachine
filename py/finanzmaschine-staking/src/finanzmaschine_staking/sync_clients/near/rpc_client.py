import base64
import json

import httpx


class RpcClient:
    BASE_URL = "https://archival-rpc.mainnet.fastnear.com"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

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

        response = self._client.post(
            self.BASE_URL,
            json={
                "jsonrpc": "2.0",
                "id": "staking",
                "method": "query",
                "params": {
                    "request_type": "call_function",
                    "account_id": contract_id,
                    "method_name": method_name,
                    "args_base64": args_base64,
                    "block_id": block_height,
                },
            },
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(
                f"NEAR RPC error: {data['error']}"
            )

        result = data["result"]["result"]

        return bytes(result)
