from trader import Trader
import asyncio
import time
from helpers import alert

# OPENING AND CLOSING SPREADS
ENTRY = 5.0
EXIT = 1


# MAIN CODE TO RUN PROGRAM
async def main():
    while True:
        try:
            t = Trader("EIGEN", ENTRY, EXIT)
            await t.run()
        except Exception as e:
            print("Error occurred:", e)
            print("Waiting for 10 minutes before retrying...")
            alert(f"Error occurred: {e}")
            alert("Waiting for 10 minutes before retrying...")
            time.sleep(600)  # Wait for 5 minutes (300 seconds) before retrying


if __name__ == "__main__":
    asyncio.run(main())
