from aevo import Aevo
from hyperliquid import Hyperliquid
import asyncio
import websockets
import json

# from calculations import calculateArb


class Trader:

    def __init__(self, balance, symbol, k):
        self.aevo = Aevo(balance / 2.0)
        self.hyperliquid = Hyperliquid(balance / 2.0)
        self.symbol = symbol
        self.in_pos = False
        self.k = k
        self.latest_aevo_book = None
        self.latest_hl_book = None
        self.aevo_updated = False
        self.hl_updated = False

    def get_aevo(self):
        return self.aevo

    def get_hyperliquid(self):
        return self.hyperliquid

    def in_pos(self):
        return self.in_pos

    def change_pos(self):
        self.in_pos = not self.in_pos

    def shortAevoLongHL(self, orderbook_aevo, orderbook_hl, k):
        aevo = self.get_aevo()
        hl = self.get_hyperliquid()
        aevo_balance = aevo.get_balance()
        hl_balance = hl.get_balance()

        aevo_bids = orderbook_aevo["bids"]
        hl_asks = orderbook_hl["levels"][1]

        aevo_orders = []
        hl_orders = []

        for i in range(min(len(aevo_bids), len(hl_asks))):
            if aevo_balance > 10 and hl_balance > 10:
                aevo_price = aevo_bids[i][0]
                aevo_vol = aevo_bids[i][1]

                hl_price = hl_asks[i]["px"]
                hl_vol = hl_asks[i]["sz"]

                est_vol = round(aevo_balance / aevo_price, 3)

                if hl_balance < est_vol * hl_price:
                    est_vol = round(hl_balance / hl_price, 3)

                vol = min(est_vol, aevo_vol, hl_vol)

                if (aevo_price - hl_price) * 100 / aevo_price > k:
                    aevo_orders.append((aevo_price, vol))
                    hl_orders.append((hl_price, vol))
                else:
                    break

                if (
                    aevo_balance - vol * aevo_price < 10
                    or hl_balance - vol * hl_price < 10
                ):
                    break

        return aevo_orders, hl_orders

    def longAevoShortHL(self, orderbook_aevo, orderbook_hl, k):
        aevo = self.get_aevo()
        hl = self.get_hyperliquid()
        aevo_balance = aevo.get_balance()
        hl_balance = hl.get_balance()

        aevo_asks = orderbook_aevo["asks"]
        hl_bids = orderbook_hl["levels"][0]

        aevo_orders = []
        hl_orders = []

        for i in range(min(len(hl_bids), len(aevo_asks))):
            if aevo_balance > 10 and hl_balance > 10:
                aevo_price = aevo_asks[i][0]
                aevo_vol = aevo_asks[i][1]

                hl_price = hl_bids[i]["px"]
                hl_vol = hl_bids[i]["sz"]

                est_vol = round(hl_balance / hl_price, 3)

                if aevo_balance < est_vol * aevo_price:
                    est_vol = round(aevo_balance / aevo_price, 3)

                vol = min(est_vol, aevo_vol, hl_vol)

                if (hl_price - aevo_price) * 100 / aevo_price > k:
                    aevo_orders.append((aevo_price, vol))
                    hl_orders.append((hl_price, vol))
                else:
                    break

                if (
                    aevo_balance - vol * aevo_price < 10
                    or hl_balance - vol * hl_price < 10
                ):
                    break

        return aevo_orders, hl_orders

    def calculateArb(self, aevo_orderbook, hl_orderbook, k):
        aevo_bid = aevo_orderbook["bids"][0][0]
        aevo_ask = aevo_orderbook["asks"][0][0]
        hl_bid = hl_orderbook["levels"][0][0]["px"]
        hl_ask = hl_orderbook["levels"][1][0]["px"]

        arb_1 = (aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask)
        arb_2 = (hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask)

        if max(arb_1, arb_2) > k:
            if arb_1 > arb_2:
                return self.shortAevoLongHL(aevo_orderbook, hl_orderbook, k)
            else:
                return self.longAevoShortHL(aevo_orderbook, hl_orderbook, k)
        else:
            return [], []

    async def fetch_aevo_orderbook(self):
        uri = "wss://ws.aevo.xyz"
        async with websockets.connect(uri) as websocket:
            subscribe_message = json.dumps(
                {"op": "subscribe", "data": [f"orderbook:{f'{self.symbol}-PERP'}"]}
            )
            await websocket.send(subscribe_message)

            async for message in websocket:
                yield json.loads(message)["data"]

    async def fetch_hyperliquid_orderbook(self):
        uri = "wss://api.hyperliquid.xyz/ws"
        async with websockets.connect(uri) as websocket:
            subscribe_message = json.dumps(
                {
                    "method": "subscribe",
                    "subscription": {"type": "l2Book", "coin": self.symbol},
                }
            )
            await websocket.send(subscribe_message)

            async for message in websocket:
                yield json.loads(message)

    async def search_arbs(self):
        aevo_book = self.fetch_aevo_orderbook()
        hl_book = self.fetch_hyperliquid_orderbook()

        async for book1, book2 in asyncio.as_completed([aevo_book, hl_book]):
            orders = self.calculateArb(book1, book2, self.k)
            # You would include your arbitrage detection and trade execution logic here
            print(orders)


async def main():
    t = Trader(100, "W", 2)

    # async for orderbook in t.fetch_aevo_orderbook():
    #     print(orderbook)
    await t.search_arbs()


if __name__ == "__main__":
    asyncio.run(main())
