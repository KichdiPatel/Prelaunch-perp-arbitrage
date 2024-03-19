import asyncio
import websockets
import json


class OrderBookStreamer:
    def __init__(self, uri, subscribe_message):
        self.uri = uri
        self.subscribe_message = subscribe_message
        self.queue = asyncio.Queue()

    async def connect_and_stream(self):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(self.subscribe_message)
            async for message in websocket:
                await self.queue.put(json.loads(message))

    async def get_next_order_book(self):
        return await self.queue.get()
