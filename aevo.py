import requests
import json
import asyncio
from loguru import logger
from aevo_api.aevo_client import AevoClient


class Aevo:

    def __init__(self, symbol):
        self.address = "0x628041b0e653F6c5995A10DC47029EeB65575396"
        self.api_key = "RtJUNks4N6Z8pZc5Jhcbu8P9YUWHfEwy"
        self.api_secret = (
            "107bf1fa85e3678ed95896f68fc2ba6a462c6b3aabdb2af82e80e3ba1c177748"
        )
        self.signing_key = (
            "0x92c9fa2ee9916cd32af718d506e8dbe59b79d708a7a9ad16c1c05fba8dd3e947"
        )
        self.balance = 0
        self.positions = []
        self.symbol = symbol
        self.instrument_ID = 0
        self.get_account()

    def get_account(self):
        url = "https://api.aevo.xyz/account"

        headers = {
            "accept": "application/json",
            "AEVO-KEY": self.api_key,
            "AEVO-SECRET": self.api_secret,
        }

        response = requests.get(url, headers=headers).json()

        # update positions
        self.positions = response["positions"]

        # update the balance
        self.balance = float(response["equity"])

        for pos in self.positions:
            self.balance -= float(pos["amount"]) * float(pos["avg_entry_price"])

        self.instrument_ID = self.fetch_instrument_ID()

    def fetch_instrument_ID(self):
        url = f"https://api.aevo.xyz/instrument/{self.symbol}-PERP"

        headers = {"accept": "application/json"}

        response = requests.get(url, headers=headers).json()
        return response["instrument_id"]

    def get_balance(self):
        return self.balance

    def get_positions(self):
        return self.positions

    async def trade(self, price, vol, direction):
        aevo = AevoClient(
            signing_key=self.signing_key,
            wallet_address=self.address,
            api_key=self.api_key,
            api_secret=self.api_secret,
            env="mainnet",
        )

        response = aevo.rest_create_order(
            instrument_id=self.instrument_ID,
            is_buy=direction == "+",
            limit_price=price,
            quantity=vol,
            post_only=False,
        )
        logger.info(response)


if __name__ == "__main__":
    # a = Aevo("W")
    # asyncio.run(a.trade(1.71, 13, "-"))
