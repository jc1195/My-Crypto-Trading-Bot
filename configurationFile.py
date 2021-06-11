# This is your RobinHood account information.
rh = {
    "username": "email",
    "password": "password",
}
# UPDATE_PRICE_INTERVALS is in milliseconds... right now it gets the prices every ten min. If you change the interval
# time, you must change the (TWO_MIN, FIVE_MIN, TEN_MIN, etc..) times as well. They relate to the interval times.
# for example, if you ran it every 2 seconds instead of every ten minutes, you would need to change TWO_MIN: 0 to 60.
# 60 is the number of "2" seconds in two min. If you ran it every 1 min, you would change TWO_MIN: 2 because there are
# 2 "1" min in two min.

# STOP_LOSS is in dollars. If the price drops more than $5, it will sell.
# RESERVE_CASH_LIMIT is the amount of money you want to leave in your RobinHood account at all times. No investment can
# be made unless there is more than $100 and enough to cover the cost of the coin/coins

# MAX_BUY_AND_SELL_LIMIT is the max amount of coins it can buy at once. MIN, is just the opposite.

# EXTREME_DAY_MAX_BUYS is the amount of times it can buy and before it sells. If it has not sold but has bought 7 times
# It will not buy anymore until it sells. Same goes for FAST, SlOW, and TURTLE conditions.

config = {
    "UPDATE_PRICE_INTERVALS": 60000,

    "MAX_BUY_AND_SELL_LIMIT": 2.0,
    "MIN_BUY_AND_SELL_LIMIT": 0.5,

    "COIN_CHOICE": "ETC",
    "ENABLE_TRADES": False,

    "EXTREME_DAY_MAX_BUYS": 7,
    "FAST_DAY_MAX_BUYS": 5,
    "SLOW_DAY_MAX_BUYS": 10,
    "TURTLE_DAY_MAX_BUYS": 3,

    "RESERVE_CASH_LIMIT": 100.00,
    "STOP_LOSS": 5.00,

    "TWO_MIN": 2,
    "FIVE_MIN": 5,
    "TEN_MIN": 10,
    "FIFTEEN_MIN": 15,
    "THIRTY_MIN": 30,

    "ONE_HOUR": 60,
    "TWO_HOUR": 120,
    "FOUR_HOUR": 240,
    "SIX_HOUR": 360,
    "EIGHTEEN_HOUR": 1080,
}
