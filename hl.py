import json
import requests
from hyperliquid.utils import constants
from eth_account.signers.local import LocalAccount
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import asyncio
from helpers import alert

"""
Hyperliquid Class that can be used to open and close trades, and get information about 
the HL Account like balance, positions, etc. 
"""


class Hyperliquid:

    # Constructor
    def __init__(self, symbol):
        with open("config.json", "r") as f:
            config = json.load(f)

        self.address = config["hl_address"]
        self.symbol = symbol

        self.real_addr = config["aevo_address"]

        account: LocalAccount = eth_account.Account.from_key(config["hl_secret_key"])
        self.exchange = Exchange(
            account, constants.MAINNET_API_URL, account_address=self.address
        )
        # self.exchange.update_leverage(2, "W")
        self.positions = []
        self.balance = 0
        self.update_acc()

    # Checks the API and updates some of the instance variables
    def update_acc(self):
        url = "https://api.hyperliquid.xyz/info"

        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "type": "clearinghouseState",
            "user": self.real_addr,
        }

        response = requests.post(url, headers=headers, data=json.dumps(data)).json()
        # update positions
        self.positions = response["assetPositions"]

        # print(response["marginSummary"])

        # update the balance
        self.balance = float(response["marginSummary"]["accountValue"]) - float(
            response["marginSummary"]["totalMarginUsed"]
        )

    # getter for self.balance
    def get_balance(self):
        return float(self.balance)

    # getter for self.positions
    def get_positions(self):
        return self.positions

    # opens a limit trade. "+" means long and "-" means short
    # having an exact trade in the opposite direction can close a trade
    async def trade(self, price, vol, direction):
        order_result = self.exchange.order(
            self.symbol, direction == "+", vol, price, {"limit": {"tif": "Ioc"}}
        )
        # self.exchange.update_leverage(2, "W")
        print(order_result)

        if "error" not in order_result["response"]["data"]["statuses"][0]:
            alert(f"MADE HYPERLIQUID SIDE TRADE \n {order_result}")

        return "error" not in order_result["response"]["data"]["statuses"][0]

    # opens a market trade. "+" means long and "-" means short
    # having an exact trade in the opposite direction can close a trade
    async def market_trade(self, vol, direction):
        result = self.exchange.market_open("ETH", direction == "+", vol, None, 0.01)
        alert("HYPERLIQUID MARKET ORDER - PLEASE REVIEW")
        return result


# if __name__ == "__main__":
#     h = Hyperliquid("W")
#     # n = (1.745, 65, "-")
#     # asyncio.run(h.trade(*n))
#     print(h.get_balance())
