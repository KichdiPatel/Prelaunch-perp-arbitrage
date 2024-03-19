from aevo import Aevo
from hyperliquid import Hyperliquid
from trader import Trader


def calculate_max_arbitrage_size_multiple(order_book_A, order_book_B, k, s):
    # Sort asks and bids
    asks_A = sorted(order_book_A["asks"], key=lambda x: x[0])
    bids_B = sorted(order_book_B["bids"], key=lambda x: x[0], reverse=True)

    total_size = 0
    total_value_bought = 0
    total_value_sold = 0

    for ask in asks_A:
        for bid in bids_B:
            if bid[0] > ask[0] and ((bid[0] - ask[0]) / ask[0] * 100) < k:
                # Calculate possible trade size without exceeding s
                trade_size = min(ask[1], bid[1], s - total_size)

                # Update totals
                total_size += trade_size
                total_value_bought += trade_size * ask[0]
                total_value_sold += trade_size * bid[0]

                # Reduce available sizes
                ask[1] -= trade_size
                bid[1] -= trade_size

                # If we've reached the maximum desired size, stop
                if total_size >= s:
                    break
            else:
                # Move to the next bid if this one doesn't provide an arbitrage opportunity
                continue
        if total_size >= s:
            break

    # Calculate final arbitrage percentage
    if total_size > 0:
        arbitrage_percentage = (
            (total_value_sold - total_value_bought) / total_value_bought * 100
        )
    else:
        arbitrage_percentage = 0

    return total_size, arbitrage_percentage


def shortAevoLongHL(trader, orderbook_aevo, orderbook_hl, k):
    aevo = trader.get_aevo()
    hl = trader.get_hyperliquid()
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

            if aevo_balance - vol * aevo_price < 10 or hl_balance - vol * hl_price < 10:
                break

    return aevo_orders, hl_orders


def longAevoShortHL(trader, orderbook_aevo, orderbook_hl, k):
    aevo = trader.get_aevo()
    hl = trader.get_hyperliquid()
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

            if aevo_balance - vol * aevo_price < 10 or hl_balance - vol * hl_price < 10:
                break

    return aevo_orders, hl_orders


def calculateArb(trader, aevo_orderbook, hl_orderbook, k):
    aevo_bid = aevo_orderbook["bids"][0][0]
    aevo_ask = aevo_orderbook["asks"][0][0]
    hl_bid = hl_orderbook["levels"][0][0]["px"]
    hl_ask = hl_orderbook["levels"][1][0]["px"]

    arb_1 = (aevo_bid - hl_ask) * 100 / max(aevo_bid, hl_ask)
    arb_2 = (hl_bid - aevo_ask) * 100 / max(hl_bid, aevo_ask)

    if max(arb_1, arb_2) > k:
        if arb_1 > arb_2:
            return shortAevoLongHL(trader, aevo_orderbook, hl_orderbook, k)
        else:
            return longAevoShortHL(trader, aevo_orderbook, hl_orderbook, k)
    else:
        return [], []


# t = Trader(100)

# order_book_B = {
#     "asks": [
#         (1.00, 5),  # Seller is willing to sell 5 tokens at a price of 100 each
#         (1.01, 10),
#         (1.02, 20),
#     ],
#     "bids": [
#         (0.99, 5),  # Buyer is willing to buy 5 tokens at a price of 99 each
#         (0.98, 10),
#         (0.97, 20),
#     ],
# }

# order_book_A = {
#     "asks": [
#         (1.05, 5),  # Seller is willing to sell 5 tokens at a price of 105 each
#         (1.06, 10),
#         (1.07, 20),
#     ],
#     "bids": [
#         (1.10, 5),  # Buyer is willing to buy 5 tokens at a price of 110 each
#         (1.09, 10),
#         (1.08, 20),
#     ],
# }
