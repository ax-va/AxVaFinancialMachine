import httpx


class TxsClient:
    BASE_URL = "https://tx.main.fastnear.com"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_function_calls(
        self,
        account_id: str,
        limit: int = 200,
    ) -> list[dict]:
        response = self._client.post(
            f"{self.BASE_URL}/v0/account",
            json={
                "account_id": account_id,
                "is_signer": True,
                "is_fucntion_call": True,
                "is_success": True,
                "limit": limit,
                "desc": False,
            }
        )
        response.raise_for_status()
        data = response.json()
        account_txs = data.get("account_txs", [])

        return account_txs

    def get_raw_txs(
        self,
        tx_hashes: list[str],
    ) -> list[dict]:
        max_num = 20
        raw_txs: list[dict] = []

        for i in range(0, len(tx_hashes), max_num):
            response = self._client.post(
                f"{self.BASE_URL}/v0/transactions",
                json={"tx_hashes": tx_hashes[i : i + max_num]},
            )
            response.raise_for_status()
            data = response.json()
            raw_txs.extend(data["transactions"])

        return raw_txs
