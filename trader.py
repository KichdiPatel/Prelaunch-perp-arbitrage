from aevo import Aevo
from hyperliquid import Hyperliquid
import asyncio
import websockets
import json

# from calculations import calculateArb


class Trader:

    def __init__(self, balance, symbol, k, exit):
        self.aevo = Aevo(symbol)
        self.hyperliquid = Hyperliquid(balance / 2.0)
        self.symbol = symbol
        self.in_position = False
        self.k = k
        self.exit = exit
        self.latest_aevo_book = None
        self.latest_hl_book = None
        self.aevo_updated = False
        self.hl_updated = False

    def get_aevo(self):
        return self.aevo

    def get_hyperliquid(self):
        return self.hyperliquid

    def in_pos(self):
        return self.in_position

    def change_pos(self):
        self.in_position = not self.in_position

    def shortAevoLongHL(self, orderbook_aevo, orderbook_hl, k, is_exit, amt=0):
        aevo = self.get_aevo()
        hl = self.get_hyperliquid()
        aevo_balance = aevo.get_balance()
        hl_balance = hl.get_balance()

        aevo_bids = orderbook_aevo["bids"]
        hl_asks = orderbook_hl["levels"][1]

        if aevo_balance > 10 and hl_balance > 10:
            aevo_price = float(aevo_bids[0][0])
            aevo_vol = float(aevo_bids[0][1])

            hl_price = float(hl_asks[0]["px"])
            hl_vol = float(hl_asks[0]["sz"])

            est_vol = round((aevo_balance - 10) / aevo_price, 3)

            if (hl_balance - 10) < est_vol * hl_price:
                est_vol = round(hl_balance / hl_price, 3)

            if is_exit:
                if (aevo_price - hl_price) * 100 / aevo_price < k:
                    vol = min(amt, aevo_vol, hl_vol)
                    return (aevo_price, vol, "-"), (hl_price, vol, "+")

            else:
                if (aevo_price - hl_price) * 100 / aevo_price > k:
                    vol = min(est_vol, aevo_vol, hl_vol)
                    return (aevo_price, vol, "-"), (hl_price, vol, "+")

    def longAevoShortHL(self, orderbook_aevo, orderbook_hl, k, is_exit, amt=0):
        aevo = self.get_aevo()
        hl = self.get_hyperliquid()
        aevo_balance = aevo.get_balance()
        hl_balance = hl.get_balance()

        aevo_asks = orderbook_aevo["asks"]
        hl_bids = orderbook_hl["levels"][0]

        if aevo_balance > 10 and hl_balance > 10:
            aevo_price = float(aevo_asks[0][0])
            aevo_vol = float(aevo_asks[0][1])

            hl_price = float(hl_bids[0]["px"])
            hl_vol = float(hl_bids[0]["sz"])

            est_vol = round(hl_balance / hl_price, 3)

            if aevo_balance < est_vol * aevo_price:
                est_vol = round(aevo_balance / aevo_price, 3)

            if is_exit:
                if (hl_price - aevo_price) * 100 / aevo_price < k:
                    vol = min(amt, aevo_vol, hl_vol)
                    return (aevo_price, vol, "+"), (hl_price, vol, "-")

            else:
                if (hl_price - aevo_price) * 100 / aevo_price > k:
                    vol = min(est_vol, aevo_vol, hl_vol)
                    return (aevo_price, vol, "+"), (hl_price, vol, "-")

    def calculateArb(self):
        aevo_orderbook = self.latest_aevo_book
        hl_orderbook = self.latest_hl_book

        aevo_bid = float(aevo_orderbook["bids"][0][0])
        aevo_ask = float(aevo_orderbook["asks"][0][0])
        hl_bid = float(hl_orderbook["levels"][0][0]["px"])
        hl_ask = float(hl_orderbook["levels"][1][0]["px"])

        arb_1 = (aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask)
        arb_2 = (hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask)

        if max(arb_1, arb_2) > self.k:
            if arb_1 > arb_2:
                return self.shortAevoLongHL(aevo_orderbook, hl_orderbook, self.k, False)
            else:
                return self.longAevoShortHL(aevo_orderbook, hl_orderbook, self.k, False)
        else:
            return (), ()

    # FIX THIS
    def calculate_close(self):
        # direction = 1 = shortAevo LongHL
        # direction = 2 = longAevo ShortHL

        for position in self.aevo.get_positions():
            aevo_orderbook = self.latest_aevo_book
            hl_orderbook = self.latest_hl_book

            if position["side"] == "sell":
                aevo_ask = float(aevo_orderbook["asks"][0][0])
                hl_bid = float(hl_orderbook["levels"][0][0]["px"])
                arb_2 = (hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask)
                if arb_2 < self.exit:
                    return self.longAevoShortHL(
                        aevo_orderbook, hl_orderbook, self.k, True
                    )

            else:
                aevo_bid = float(aevo_orderbook["bids"][0][0])
                hl_ask = float(hl_orderbook["levels"][1][0]["px"])
                arb_1 = (aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask)
                if arb_1 < self.exit:
                    return self.shortAevoLongHL(
                        aevo_orderbook, hl_orderbook, self.k, True
                    )

        return (), ()

    async def fetch_order_book(self, uri, subscribe_message, set_latest_book):
        async with websockets.connect(uri) as websocket:
            await websocket.send(subscribe_message)
            async for message in websocket:
                set_latest_book(json.loads(message))
                # No event set here, the flags in set_latest_book will indicate new data

    async def fetch_aevo_orderbook(self):
        aevo_uri = "wss://ws.aevo.xyz"
        subscribe_message = json.dumps(
            {"op": "subscribe", "data": [f"orderbook:{f'{self.symbol}-PERP'}"]}
        )
        await self.fetch_order_book(aevo_uri, subscribe_message, self.set_aevo_book)

    async def fetch_hyperliquid_orderbook(self):
        hl_uri = "wss://api.hyperliquid.xyz/ws"
        subscribe_message = json.dumps(
            {
                "method": "subscribe",
                "subscription": {"type": "l2Book", "coin": self.symbol},
            }
        )
        await self.fetch_order_book(hl_uri, subscribe_message, self.set_hl_book)

    def set_aevo_book(self, book):
        if (
            "bids" in book["data"]
            and "asks" in book["data"]
            and len(book["data"]["bids"]) > 1
            and len(book["data"]["asks"]) > 1
        ):
            self.latest_aevo_book = book["data"]
            self.aevo_updated = True

    def set_hl_book(self, book):
        self.latest_hl_book = book["data"]
        self.hl_updated = True

    def make_trade(self, aevo, hl):
        self.in_position = False
        print("made trade")

    async def search_arbs(self):
        while True:
            # Short sleep to yield control and prevent a busy loop
            await asyncio.sleep(1)
            # self.latest_aevo_book
            # self.latest_hl_book
            # print(self.latest_aevo_book)
            if self.aevo_updated and self.hl_updated:
                aevo_ord, hl_ord = self.calculateArb()
                print(aevo_ord)
                print(hl_ord)
                self.make_trade(aevo_ord, hl_ord)

                aevo_close, hl_close = self.calculateArb()
                print(aevo_close)
                print(hl_close)
                self.make_trade(aevo_close, hl_close)

                # Reset update flags after processing
                self.aevo_updated = False
                self.hl_updated = False

    async def run(self):
        # Initiate tasks for fetching order books and searching for arbitrage opportunities
        tasks = [
            asyncio.create_task(self.fetch_aevo_orderbook()),
            asyncio.create_task(self.fetch_hyperliquid_orderbook()),
            asyncio.create_task(self.search_arbs()),
        ]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)


async def main():
    t = Trader(100, "W", 0.5)

    # async for orderbook in t.fetch_aevo_orderbook():
    #     print(orderbook)
    await t.run()


if __name__ == "__main__":
    asyncio.run(main())
