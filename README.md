# Pre-launch Perpetuals Arbitrage Bot

## The Arbitrage

In researching airdrops and TGE, I came across these pre-launch markets like on kucoin, whales market, aevo, and hyperliquid. Because these are speculative markets on future prices, and a new crypto product, they didn't have a massive amount of volume. Initially I watched and researched these exchanges before the Wormhole airdrop, and noticed there were very clear fluctuations in the spread between exchanges where an arbitrage opportunity could take place. I decided for this project to use Aevo and Hyperliquid as they had they had decent opportunities and good API documentation for this proof-of-concept project. So, this is a bot to capture arbitrage between these pre-launch perpetuals between Aevo and Hyperliquid. After finishing this project, there was not a lot of time to robustly test this project before liquidity started to move away from these perpetuals and hyperliquid stopped adding new perps. So, I was able to make a little money, but not enough to get rich... which is why I am posting it on github haha. It was still a really interesting project and hope whoever reads this can gain some inspiration for a similar idea.

## The Logic

The code is structured with aevo.py and hl.py which are classes that can be used to access information and interact with the aevo/hyperliquid exchange APIs. This includes making limit/market trades, getting balances, etc. The main trade logic is in trader.py.

Here's how the trade algorithm works. Both exchanges provide websocket apis for orderbooks which update as instance variables in the trader class. Only when both websockets have been updated and have not yet been looked at, the program will search for arbs in the orderbook. If an arbitrage is identified in either direction, a trade is placed where there is a short trade on one, and a long trade on the other. Both are trading perpetuals on the same pre-TGE token for example "W" or "EIGEN" which is why this works. If one leg of the trade is successful and the other is not, then the trade that was successful will close out. This is why the main risk in this strategy is execution since you would lose money closing out that leg of the trade. Once the program has entered a trade, it will continuosly search the orderbooks for potentially new arbs to enter or closing arbs for the existing positions.

There is a lot more to it, but this is a high level overview. Go through the code to get more of an understanding! Hope you enjoy!
