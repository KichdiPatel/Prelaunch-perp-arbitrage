import asyncio
import websockets
import json


class Trader:
    def __init__(self, symbol, k):
        self.symbol = symbol
        self.k = k
        self.latest_aevo_book = None
        self.latest_hl_book = None
        self.aevo_updated = False
        self.hl_updated = False

    async def fetch_order_book(self, uri, subscribe_message, set_latest_book):
        async with websockets.connect(uri) as websocket:
            await websocket.send(subscribe_message)
            async for message in websocket:
                set_latest_book(json.loads(message))
                # No event set here, the flags in set_latest_book will indicate new data

    async def fetch_aevo_orderbook(self):
        aevo_uri = "wss://ws.aevo.xyz"
        subscribe_message = json.dumps(
            {"op": "subscribe", "data": [f"orderbook:{self.symbol}"]}
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
        self.latest_aevo_book = book
        self.aevo_updated = True

    def set_hl_book(self, book):
        self.latest_hl_book = book
        self.hl_updated = True

    async def search_arbs(self):
        while True:
            # Short sleep to yield control and prevent a busy loop
            await asyncio.sleep(1)
            if self.aevo_updated and self.hl_updated:
                orders = self.calculateArb(self.latest_aevo_book, self.latest_hl_book)
                print(orders)
                # Reset update flags after processing
                self.aevo_updated = False
                self.hl_updated = False
                # Implement action based on the arbitrage calculation result

    def calculateArb(self, book1, book2):
        # Placeholder for arbitrage calculation logic.
        # Return value should be the arbitrage orders to execute based on the input books.
        # This is just a simple implementation for illustration.
        # Your actual calculation will depend on the specifics of the order book data and your strategy.
        return "Arbitrage opportunity based on latest books."

    async def run(self):
        # Initiate tasks for fetching order books and searching for arbitrage opportunities
        tasks = [
            asyncio.create_task(self.fetch_aevo_orderbook()),
            asyncio.create_task(self.fetch_hyperliquid_orderbook()),
            asyncio.create_task(self.search_arbs()),
        ]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)


# Example usage
async def main():
    symbol = "ETH"  # Example symbol
    k = 0.01  # Example threshold for arbitrage calculation
    trader = Trader(symbol, k)
    await trader.run()


if __name__ == "__main__":
    asyncio.run(main())
