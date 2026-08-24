import httpx


class NearTransactionsClient:
    BASE_URL = "https://tx.main.fastnear.com"

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def get_account_transactions(
        self,
        account_id: str,
    ) -> dict:
        response = self._client.post(
            f"{self.BASE_URL}/v0/account",
            json={
                "account_id": account_id,
                "is_signer": True,
                "is_fucntion_call": True,
                "is_success": True,
                "limit": 200,
                "desc": False,
            }
        )
        response.raise_for_status()

        return response.json()

    def get_transactions(
        self,
        tx_hashes: list[str],
    ) -> list[dict]:
        max_num = 20
        transactions: list[dict] = []

        for i in range(0, len(tx_hashes), max_num):
            response = self._client.post(
                f"{self.BASE_URL}/v0/transactions",
                json={"tx_hashes": tx_hashes[i : i + max_num]},
            )
            response.raise_for_status()
            data = response.json()
            transactions.extend(data["transactions"])

        return transactions
