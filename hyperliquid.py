import json
import requests


class Hyperliquid:

    def __init__(self):
        self.balance = 0
        self.positions = []
        self.address = "0xa22Bd4b5b230B2C47Dcae285d89892b574e99e9C"

        self.get_account()

    def get_account(self):
        url = "https://api.hyperliquid.xyz/info"

        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "type": "clearinghouseState",
            "user": self.address,
        }

        response = requests.post(url, headers=headers, data=json.dumps(data)).json()

        # update positions
        self.positions = response["assetPositions"]

        # update the balance
        self.balance = float(response["marginSummary"]["accountValue"]) - float(
            response["marginSummary"]["totalNtlPos"]
        )

    def get_balance(self):
        return self.balance

    def get_positions(self):
        return self.positions
