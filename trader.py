from aevo import Aevo
from hl import Hyperliquid
import asyncio
import websockets
import json
from helpers import alert

# from calculations import calculateArb

"""
This is where the main logic for the trading is happening. 
"""

STEP_SIZE = 0
LEVERAGE = 1


class Trader:
    # Constructor
    def __init__(self, symbol, k, exit):
        self.aevo = Aevo(symbol)
        self.hyperliquid = Hyperliquid(symbol)
        self.symbol = symbol
        self.in_position = False
        self.k = k
        self.exit = exit
        self.latest_aevo_book = None
        self.latest_hl_book = None
        self.aevo_updated = False
        self.hl_updated = False
        self.in_position = not self.in_position

    # updating all the accounts
    def update_accounts(self):
        self.aevo.update_acc()
        self.hyperliquid.update_acc()

    """
    Makes an Arb trade where you short on aevo and long on hyperliquid. This
    can also be used as a closing trade if the opposing trade was used to open
    the arbitrage. 
    """

    def shortAevoLongHL(self, orderbook_aevo, orderbook_hl, k, is_exit, amt=0):
        aevo = self.aevo
        hl = self.hyperliquid
        aevo_balance = aevo.get_balance() * LEVERAGE * 0.85
        hl_balance = hl.get_balance() * LEVERAGE * 0.85

        # gets the orderbook data
        aevo_bids = orderbook_aevo["bids"]
        hl_asks = orderbook_hl["levels"][1]
        # print(aevo_balance > 15)
        # print(hl_balance)

        # Checks to enter a trade only if the balance is above minimum threshold
        # or you are using the trade to exit a position
        if (aevo_balance > 15 and hl_balance > 15) or is_exit:

            # calculating the estimated trade
            aevo_price = float(aevo_bids[0][0])
            aevo_vol = float(aevo_bids[0][1])
            hl_price = float(hl_asks[0]["px"])
            hl_vol = float(hl_asks[0]["sz"])
            est_vol = round((aevo_balance - 10) / aevo_price, 3)

            if (hl_balance - 10) < est_vol * hl_price:
                est_vol = round(hl_balance / hl_price, 3)

            # calculate the trade if it is an exit position
            if is_exit:
                if (aevo_price - hl_price) * 100 / aevo_price < k:
                    vol = min(amt, aevo_vol, hl_vol)
                    vol = round(vol, STEP_SIZE)

                    return (aevo_price, vol, "-"), (hl_price, vol, "+")

            # calculate the trade if it is a opening position
            else:
                if (aevo_price - hl_price) * 100 / aevo_price > k:
                    vol = min(est_vol, aevo_vol, hl_vol)
                    vol = round(vol, STEP_SIZE)
                    return (aevo_price, vol, "-"), (hl_price, vol, "+")

        return (), ()

    """
    Makes an Arb trade where you long on aevo and short on hyperliquid. This
    can also be used as a closing trade if the opposing trade was used to open
    the arbitrage. 
    """

    def longAevoShortHL(self, orderbook_aevo, orderbook_hl, k, is_exit, amt=0):

        aevo = self.aevo
        hl = self.hyperliquid
        aevo_balance = aevo.get_balance() * LEVERAGE * 0.85
        hl_balance = hl.get_balance() * LEVERAGE * 0.85

        aevo_asks = orderbook_aevo["asks"]
        hl_bids = orderbook_hl["levels"][0]

        # Checks to enter a trade only if the balance is above minimum threshold
        # or you are using the trade to exit a position
        if (aevo_balance > 15 and hl_balance > 15) or is_exit:
            # calculating the estimated trade
            aevo_price = float(aevo_asks[0][0])
            aevo_vol = float(aevo_asks[0][1])
            hl_price = float(hl_bids[0]["px"])
            hl_vol = float(hl_bids[0]["sz"])
            est_vol = round(hl_balance / hl_price, 3)

            if aevo_balance < est_vol * aevo_price:
                est_vol = round(aevo_balance / aevo_price, 3)

            # calculate the trade if it is an exit position
            if is_exit:
                if (hl_price - aevo_price) * 100 / aevo_price < k:
                    vol = min(amt, aevo_vol, hl_vol)
                    vol = round(vol, STEP_SIZE)
                    return (aevo_price, vol, "+"), (hl_price, vol, "-")

            # calculate the trade if it is a opening position
            else:
                if (hl_price - aevo_price) * 100 / aevo_price > k:
                    vol = min(est_vol, aevo_vol, hl_vol)
                    vol = round(vol, STEP_SIZE)
                    return (aevo_price, vol, "+"), (hl_price, vol, "-")

        return (), ()

    # calculates what the arbitrage opportunity is (if any) checking in both long/short direction
    def calculateArb(self):
        aevo_orderbook = self.latest_aevo_book
        hl_orderbook = self.latest_hl_book

        aevo_bid = float(aevo_orderbook["bids"][0][0])
        aevo_ask = float(aevo_orderbook["asks"][0][0])
        hl_bid = float(hl_orderbook["levels"][0][0]["px"])
        hl_ask = float(hl_orderbook["levels"][1][0]["px"])

        arb_1 = (aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask)
        arb_2 = (hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask)

        print(f"Max arb = {max(arb_1, arb_2)}")

        if max(arb_1, arb_2) > self.k:
            if arb_1 > arb_2:
                return self.shortAevoLongHL(aevo_orderbook, hl_orderbook, self.k, False)
            else:
                return self.longAevoShortHL(aevo_orderbook, hl_orderbook, self.k, False)
        else:
            return (), ()

    # FIX THIS
    # calculates the closing position for open trades
    def calculate_close(self):
        # direction = 1 = shortAevo LongHL
        # direction = 2 = longAevo ShortHL

        for position in self.aevo.get_positions():
            aevo_orderbook = self.latest_aevo_book
            hl_orderbook = self.latest_hl_book
            amount = float(position["amount"])
            if position["side"] == "sell":
                aevo_ask = float(aevo_orderbook["asks"][0][0])
                hl_bid = float(hl_orderbook["levels"][0][0]["px"])
                arb_2 = abs((hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask))
                print(f"Closing arb = {arb_2}")
                if arb_2 < self.exit:
                    return self.longAevoShortHL(
                        aevo_orderbook, hl_orderbook, self.exit, True, amount
                    )

            else:
                aevo_bid = float(aevo_orderbook["bids"][0][0])
                hl_ask = float(hl_orderbook["levels"][1][0]["px"])
                arb_1 = abs((aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask))
                print(f"Closing arb = {arb_1}")
                if arb_1 < self.exit:
                    return self.shortAevoLongHL(
                        aevo_orderbook, hl_orderbook, self.exit, True, amount
                    )

        return (), ()

    # Fetches orderbook from websocket
    async def fetch_order_book(self, uri, subscribe_message, set_latest_book):
        async with websockets.connect(uri) as websocket:
            await websocket.send(subscribe_message)
            async for message in websocket:
                set_latest_book(json.loads(message))
        # attempt_count = 0
        # max_attempts = 5  # Max number of reconnection attempts
        # while attempt_count < max_attempts:
        #     try:

        #     except websockets.exceptions.ConnectionClosedError as e:
        #         print(
        #             f"WebSocket connection closed: {e}, attempting to reconnect ({attempt_count+1}/{max_attempts})"
        #         )
        #         alert(
        #             f"WebSocket connection closed: {e}, attempting to reconnect ({attempt_count+1}/{max_attempts})"
        #         )
        #         attempt_count += 1
        #         await asyncio.sleep(
        #             2
        #         )  # Wait for 2 seconds before attempting to reconnect
        #     else:
        #         break  # If no exceptions were raised, exit the loop

    # utilizes fetch_order_book() to get Aevo Websocket API orderbook data
    async def fetch_aevo_orderbook(self):
        aevo_uri = "wss://ws.aevo.xyz"
        subscribe_message = json.dumps(
            {"op": "subscribe", "data": [f"orderbook:{f'{self.symbol}-PERP'}"]}
        )
        await self.fetch_order_book(aevo_uri, subscribe_message, self.set_aevo_book)

    # utilizes fetch_order_book() to get Hyperliquid Websocket API orderbook data
    async def fetch_hyperliquid_orderbook(self):
        hl_uri = "wss://api.hyperliquid.xyz/ws"
        subscribe_message = json.dumps(
            {
                "method": "subscribe",
                "subscription": {"type": "l2Book", "coin": self.symbol},
            }
        )
        await self.fetch_order_book(hl_uri, subscribe_message, self.set_hl_book)

    # setter for aevo orderbook data
    def set_aevo_book(self, book):
        if (
            "bids" in book["data"]
            and "asks" in book["data"]
            and len(book["data"]["bids"]) > 1
            and len(book["data"]["asks"]) > 1
        ):
            self.latest_aevo_book = book["data"]
            self.aevo_updated = True

    # setter for hyperliquid orderbook data
    def set_hl_book(self, book):
        # if (
        #     "levels" in book
        #     and len(book["levels"][0]) > 1
        #     and len(book["levels"][1]) > 1
        # ):
        self.latest_hl_book = book["data"]
        self.hl_updated = True

    # Opens the arbitrage trade
    async def open_trade(self, _aevo, _hl):
        print(f"trade params = {_aevo} and {_hl}")
        aevo_trade, hl_trade = await asyncio.gather(
            self.aevo.trade(*_aevo), self.hyperliquid.trade(*_hl)
        )
        print(f"finsished trade attempt. Aevo: {aevo_trade}, HL: {hl_trade}")

        # If trades fail on both exchanges don't need to do anything
        if not aevo_trade and not hl_trade:
            print("No trade...")

        # If a trade fails on one of the exchanges, then close out of the one that succeeded
        elif not (aevo_trade and hl_trade):
            long_price = max(_aevo[0], _hl[0]) * (1 - ((self.k - 1) / 100))
            short_price = min(_aevo[0], _hl[0]) * (1 + ((self.k - 1) / 100))

            if aevo_trade == False:
                if _aevo[2] == "+":
                    direction = "-"
                    success = await self.aevo.trade(short_price, _aevo[1], "+")

                else:
                    direction = "+"
                    success = await self.aevo.trade(long_price, _aevo[1], "-")

                if success:
                    self.update_accounts()
                    print("MADE TRADE")
                    alert("ARBITRAGE STARTED!!!")
                else:
                    self.aevo.market_order(_aevo[1], direction)
                    self.update_accounts()
                    alert(
                        "HAD TO MARKET CLOSE AEVO SIDE WHILE TRYING TO START - PLEASE REVIEW!!!"
                    )

            else:
                if _hl[2] == "+":
                    direction = "-"
                    success = await self.aevo.trade(short_price, _hl[1], "+")
                else:
                    direction = "+"
                    success = await self.aevo.trade(long_price, _hl[1], "-")

                if success:
                    self.update_accounts()
                    print("Made Trade")
                    alert("ARBITRAGE STARTED!!!")
                else:
                    self.hyperliquid.market_trade(_hl[1], direction)
                    self.update_accounts()
                    alert(
                        "HAD TO MARKET CLOSE HYPERLIQUID SIDE WHILE TRYING TO START - PLEASE REVIEW!!!"
                    )
        # if both trades were successful, then arbitrage has been opened
        else:
            self.update_accounts()
            alert("ARBITRAGE BEGUN!!!!")
            print("Made trade!")

    # Closes the arbitrage trade
    async def close_trade(self, _aevo, _hl):
        aevo_trade, hl_trade = await asyncio.gather(
            self.aevo.trade(*_aevo), self.hyperliquid.trade(*_hl)
        )

        # If trades fail on both exchanges don't need to do anything
        if not aevo_trade and not hl_trade:
            print("close didn't work for both...")

        # If a trade fails on one of the exchanges, then close out of the one that succeeded
        elif not (aevo_trade and hl_trade):
            if aevo_trade == False:
                if _aevo[2] == "+":
                    direction = "-"
                else:
                    direction = "+"

                self.aevo.market_order(_aevo[1], direction)
                alert("MARKET CLOSED ARB OP - AEVO SIDE")
                self.update_accounts()

            else:
                if _hl[2] == "+":
                    direction = "-"
                else:
                    direction = "+"

                self.hyperliquid.market_trade(_hl[1], direction)
                alert("MARKET CLOSED ARB OP - HYPERLIQUID SIDE")
                self.update_accounts()
        else:
            self.update_accounts()
            alert("ARBITRAGE CLOSED!!!!")
            print("Made trade!")

    # This function is what is constantly looking for arbs and plcing orders
    async def search_arbs(self):
        while True:
            # Short sleep to yield control and prevent a busy loop
            await asyncio.sleep(1)
            # self.latest_aevo_book
            # self.latest_hl_book
            # print(self.latest_aevo_book)
            if self.aevo_updated and self.hl_updated:
                # print("running...")
                aevo_ord, hl_ord = self.calculateArb()
                # print(aevo_ord)
                # print(hl_ord)
                if len(aevo_ord) > 0 and len(hl_ord) > 0:
                    await self.open_trade(aevo_ord, hl_ord)
                aevo_close, hl_close = self.calculate_close()
                # print(aevo_close)
                # print(hl_close)
                if len(aevo_close) > 0 and len(hl_close) > 0:
                    # print("Porentially closing...")
                    await self.close_trade(aevo_close, hl_close)

                # Reset update flags after processing
                self.aevo_updated = False
                self.hl_updated = False

    # main function for running everything. New arbs are only searched for when both orderbooks have been updated
    # and neither has been searched for an arb yet
    async def run(self):
        # Initiate tasks for fetching order books and searching for arbitrage opportunities
        tasks = [
            asyncio.create_task(self.fetch_aevo_orderbook()),
            asyncio.create_task(self.fetch_hyperliquid_orderbook()),
            asyncio.create_task(self.search_arbs()),
        ]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        # try:
        #     await asyncio.gather(*tasks)
        # except Exception as e:
        #     print(f"Error encountered: {e}")
        #     alert(f"Error encountered: {e}")


# async def main():
#     t = Trader("W", 2, 0.2)

#     # async for orderbook in t.fetch_aevo_orderbook():
#     #     print(orderbook)
#     await t.run()


# if __name__ == "__main__":
#     asyncio.run(main())
