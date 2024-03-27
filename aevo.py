import requests
import json
from decimal import Decimal
import random
import time
import asyncio


class Aevo:

    def __init__(self, symbol):
        self.address = "0xa22Bd4b5b230B2C47Dcae285d89892b574e99e9C"
        self.api_key = "cXJUzUqZHinhuXVhKz8MZ18Xu6Rt86mJ"
        self.api_secret = (
            "e453893d6fbed68b6c8068f0ba9953c0c2e9d4b63ae8867e03a9e326954b5931"
        )
        self.signing_key = (
            "0xfe43590eb65560142f50b65f994c5c3372aded90de40995a1a3498a237616ca9"
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

    def trade(self, price, vol, direction):
        url = "https://api.aevo.xyz/orders"
        amt = Decimal(str(vol))
        limit = Decimal(str(price))

        payload = {
            "instrument": self.instrument_ID,
            "maker": self.address,
            "is_buy": direction == "+",
            "amount": int(amt * (10**6)),
            "limit_price": int(limit * (10**6)),
            "salt": random.randint(10000000, 99999999),
            "signature": self.signing_key,
            "timestamp": str(int(time.time())),
        }
        print(payload)
        headers = headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "AEVO-KEY": self.api_key,
            "AEVO-SECRET": self.api_secret,
        }

        response = requests.post(url, json=payload, headers=headers)

        print(response.text)


a = Aevo("W")
a.trade(1.73, 2, "+")
