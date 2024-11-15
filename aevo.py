import requests
import json
import asyncio
from loguru import logger
from aevo_api.aevo_client import AevoClient
from helpers import alert

"""
Aevo Class that can be used to open and close trades, and get information about 
the Aevo Account like balance, positions, etc. 
"""


class Aevo:

    # Constructor
    def __init__(self, symbol):
        with open("config.json", "r") as f:
            config = json.load(f)

        self.symbol = symbol
        self.address = config["aevo_address"]
        self.api_key = config["aevo_api_key"]
        self.api_secret = config["aevo_api_secret"]
        self.signing_key = config["aevo_signing_key"]
        self.instrument_ID = self.fetch_instrument_ID()

        self.positions = []
        self.balance = 0
        self.update_acc()

    # Checks the API and updates some of the instance variables
    def update_acc(self):
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
        self.balance = response["collaterals"][0]["available_balance"]

    # gets the instrument ID of a particular symbol
    def fetch_instrument_ID(self):
        url = f"https://api.aevo.xyz/instrument/{self.symbol}-PERP"

        headers = {"accept": "application/json"}

        response = requests.get(url, headers=headers).json()
        return response["instrument_id"]

    # getter for self.balance
    def get_balance(self):
        return float(self.balance)

    # getter for self.positions
    def get_positions(self):
        return self.positions

    # opens a limit trade on aevo. "+" means long and "-" means short
    # having an exact trade in the opposite direction can close a trade
    async def trade(self, price, vol, direction):
        print(price, vol, direction)
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
        # logger.info(response)
        if "error" not in response:
            alert(f"MADE AEVO SIDE TRADE \n {response}")

        print(response)
        return "error" not in response

    # opens a market trade on aevo. "+" means long and "-" means short
    # having an exact trade in the opposite direction can close a trade
    async def market_order(self, vol, direction):
        aevo = AevoClient(
            signing_key=self.signing_key,
            wallet_address=self.address,
            api_key=self.api_key,
            api_secret=self.api_secret,
            env="mainnet",
        )

        response = aevo.rest_create_market_order(
            instrument_id=1, is_buy=direction == "+", quantity=vol
        )

        alert("AEVO MARKET ORDER - PLEASE REVIEW")
        return response


# if __name__ == "__main__":
#     a = Aevo("W")
#     # n = (1.72, 71.965, "+")
#     # asyncio.run(a.trade(*n))
#     print(a.get_balance())
