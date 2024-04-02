from trader import Trader
import asyncio


async def main():

    try:
        t = Trader("W", 4, 1)
        await t.run()
    except:
        print("error encountered... trying again")
        try:
            t = Trader("W", 4, 1)
            await t.run()
        except:
            print("error encountered again... closing")


if __name__ == "__main__":
    asyncio.run(main())
