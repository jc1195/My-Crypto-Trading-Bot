import datetime
import pickle
import numpy
import robin_stocks.robinhood.account

import configurationFile
import pricesAndAverages
import pandas as pd
import os.path as path

global count, boughtInData, soldData, messageData, boughtDataOld

CRYPTO_CHOICE = configurationFile.config['COIN_CHOICE']
EXTREME_DAY_MAX_BUYS = configurationFile.config['EXTREME_DAY_MAX_BUYS']
FAST_DAY_MAX_BUYS = configurationFile.config['FAST_DAY_MAX_BUYS']
SLOW_DAY_MAX_BUYS = configurationFile.config['SLOW_DAY_MAX_BUYS']
TURTLE_DAY_MAX_BUYS = configurationFile.config['TURTLE_DAY_MAX_BUYS']

MAX_BUY_AND_SELL_LIMIT = configurationFile.config['MAX_BUY_AND_SELL_LIMIT']
MIN_BUY_AND_SELL_LIMIT = configurationFile.config['MIN_BUY_AND_SELL_LIMIT']

TRADING_BUFFER = 0.10
SELLING_TRADING_BUFFER = 0.05
RESERVE_CASH_LIMIT = configurationFile.config['RESERVE_CASH_LIMIT']
STOP_LOSS = configurationFile.config['STOP_LOSS']

ONE_HOUR = configurationFile.config['ONE_HOUR']
TWO_HOUR = configurationFile.config['TWO_HOUR']

differenceInMinBought = 0.0
differenceInMinSold = 0.0
count = 0


# This method decided which trading strategy is to be used. Right now it is only using slow day because I am testing a
# new coin. Originally I was trading ETC, now I am trading LTC.
def runTrades(run=False):
    global boughtInData, count
    twentyPercentBelowOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 20), 3)
    twentyPercentAboveOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 80), 3)

    if run:
        slowDay()
        # if 5.0 <= (twentyPercentAboveOneHour - twentyPercentBelowOneHour):
        #     extremeDay()
        # # Hold -------
        # elif 4.50 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) < 5.0:
        #     holdTrade()
        # elif 2.5 <= (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 4.50:
        #     fastDay()
        # # Hold ----------
        # elif 2.0 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) < 2.5:
        #     holdTrade()
        # elif 1.0 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 2.0:
        #     slowDay()
        # elif (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 1.0:
        #     turtleDay()
    else:
        return


# Checks to see if the prices meet the extreme day conditions to buy or sell. Currently Extreme day conditions are
# prices that are greater or less than $5 moving averages in 1 hour.
def extremeDay():
    global boughtInData, count, messageData, boughtDataOld
    price = pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]
    if boughtInData.empty:
        profitCheck = 0.0
        lastBoughtPrice = 0.0
        lastSoldPrice = 0.0
        sellCheck = False
        lastTime = 1.0
    else:
        profitCheck = (boughtInData["Total"].sum())
        lastBoughtPrice = (boughtDataOld['Price'].tail(count).max() + 0.15)
        index = boughtInData["Price"][::-1].idxmin()
        lastSoldPrice = boughtInData.at[index, "Price"]
        count = boughtInData.iloc[-1]['Count']

        # Get last execution time
        lastExec = boughtInData.iloc[-1]['exec_time']
        lastTime = getTimeToSec(time=lastExec)

        # If false, I'm either losing money or bought before I sold.
        futureProfit = (-price * 0.5) + profitCheck
        if profitCheck < 0:
            if futureProfit < profitCheck:
                sellCheck = True
            else:
                sellCheck = False
        else:
            sellCheck = False

    price = pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]
    EMATwo = pricesAndAverages.getData().iloc[-1]["EMA-2"]
    EMAFive = pricesAndAverages.getData().iloc[-1]["EMA-5"]
    EMATen = pricesAndAverages.getData().iloc[-1]["EMA-10"]
    EMAFifteen = pricesAndAverages.getData().iloc[-1]["EMA-15"]
    EMAThirty = pricesAndAverages.getData().iloc[-1]["EMA-30"]
    EMASixty = pricesAndAverages.getData().iloc[-1]["EMA-60"]
    RSITwo = pricesAndAverages.getData().iloc[-1]["RSI-2"]
    RSIFive = pricesAndAverages.getData().iloc[-1]["RSI-5"]
    RSITen = pricesAndAverages.getData().iloc[-1]["RSI-10"]
    RSIFifteen = pricesAndAverages.getData().iloc[-1]["RSI-15"]
    RSIThirty = pricesAndAverages.getData().iloc[-1]["RSI-30"]
    RSISixty = pricesAndAverages.getData().iloc[-1]["RSI-60"]
    MATwo = pricesAndAverages.getData().iloc[-1]["MA-2"]
    MAFive = pricesAndAverages.getData().iloc[-1]["MA-5"]
    MATen = pricesAndAverages.getData().iloc[-1]["MA-10"]
    MAFifteen = pricesAndAverages.getData().iloc[-1]["MA-15"]
    MAThirty = pricesAndAverages.getData().iloc[-1]["MA-30"]
    MASixty = pricesAndAverages.getData().iloc[-1]["MA-60"]
    twentyPercentBelowOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 20), 3)
    twentyPercentAboveOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 80), 3)

    # EXTREME: Buying conditions

    if price > MATwo > EMAFive > EMATen \
            and RSITwo > 60 \
            and lastTime > 1.0 \
            and count < EXTREME_DAY_MAX_BUYS \
            or price > MATwo > EMAFive > EMATen > EMAFifteen \
            and RSITwo > 60 \
            and lastTime > 1.0 \
            and count >= EXTREME_DAY_MAX_BUYS \
            and price < twentyPercentAboveOneHour \
            or price < twentyPercentBelowOneHour \
            and RSITwo < 50 \
            and price < MATwo < EMAFive < EMATen \
            and lastTime > 30.0:
        updateMessageData(text=("EXTREME: Condition met to buy for the price of $"
                                + str(round((price + TRADING_BUFFER), 2))
                                + ". Count at " + str(count)))
        buy(condition=True, buyAmount=EXTREME_DAY_MAX_BUYS)
    else:
        buy(condition=False)

    # EXTREME: Selling conditions
    if sellCheck == True \
            and price > lastBoughtPrice > 1.1 \
            and price > MATwo < EMAFive < EMATen \
            and lastTime > 0.3 \
            and count < EXTREME_DAY_MAX_BUYS \
            or price > lastBoughtPrice > 1.1 \
            and sellCheck == True \
            and price > MATwo > EMAFive > EMATen > EMAFifteen \
            and RSITwo > 65 \
            and lastTime > 1.0 \
            and count < EXTREME_DAY_MAX_BUYS \
            or count == EXTREME_DAY_MAX_BUYS \
            and price < (lastBoughtPrice - STOP_LOSS) \
            and price < MATwo < EMAFive < EMATen < EMAFifteen \
            and differenceInMinSold > 90.0:
        updateMessageData(text=("EXTREME: Condition met to sell for the price of $"
                                + str(round(price, 2))
                                + ". Count at " + str(count)))
        sell(condition=True, sellAmount=EXTREME_DAY_MAX_BUYS)
    else:
        sell(condition=False)


# Checks to see if the prices meet the fast day conditions to buy or sell. Currently Extreme day conditions are
# prices that are greater than $3 but less than $4.50 moving averages in 1 hour.
def fastDay():
    global boughtInData, count, messageData, boughtDataOld
    price = pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]
    if boughtInData.empty:
        # profitCheck = 0.0
        lastBoughtPrice = 0.0
        # lastSoldPrice = 0.0
        # sellCheck = False
        lastTime = 1.0
    else:
        # profitCheck = (boughtInData["Total"].sum())
        lastBoughtPrice = (boughtDataOld['Price'].tail(count).max() + 0.15)
        count = boughtInData.iloc[-1]['Count']

        # Get last execution time
        lastExec = boughtInData.iloc[-1]['exec_time']
        lastTime = getTimeToSec(time=lastExec)

        # If false, I'm either losing money or bought before I sold.
        # futureProfit = (-price * 0.5) + profitCheck
        # if profitCheck < 0:
        #     if futureProfit < profitCheck:
        #         sellCheck = True
        #     else:
        #         sellCheck = False
        # else:
        #     sellCheck = False

    # # EMATwo = botFile.getData().iloc[-1]["EMA-2"]
    # # EMAFive = botFile.getData().iloc[-1]["EMA-5"]
    # EMATen = botFile.getData().iloc[-1]["EMA-10"]
    # # EMAFifteen = botFile.getData().iloc[-1]["EMA-15"]
    EMAThirty = pricesAndAverages.getData().iloc[-1]["EMA-30"]
    # EMASixty = botFile.getData().iloc[-1]["EMA-60"]
    # # RSITwo = botFile.getData().iloc[-1]["RSI-2"]
    # # RSIFive = botFile.getData().iloc[-1]["RSI-5"]
    # RSITen = botFile.getData().iloc[-1]["RSI-10"]
    # # RSIFifteen = botFile.getData().iloc[-1]["RSI-15"]
    # RSIThirty = botFile.getData().iloc[-1]["RSI-30"]
    # RSISixty = botFile.getData().iloc[-1]["RSI-60"]
    # # MATwo = botFile.getData().iloc[-1]["MA-2"]
    # # MAFive = botFile.getData().iloc[-1]["MA-5"]
    # MATen = botFile.getData().iloc[-1]["MA-10"]
    # # MAFifteen = botFile.getData().iloc[-1]["MA-15"]
    # MAThirty = botFile.getData().iloc[-1]["MA-30"]
    # MASixty = botFile.getData().iloc[-1]["MA-60"]

    twentyPercentBelowOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 20), 3)
    twentyPercentAboveOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 80), 3)
    standardDeviation = (round(float(numpy.std(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3))
    averagePrice = round(float(numpy.mean(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3)

    # FAST: Buying conditions
    if price < (EMAThirty - standardDeviation) \
            and count < FAST_DAY_MAX_BUYS \
            and lastTime > 3.0:
        updateMessageData(text=("FAST: Condition met to buy for the price of $"
                                + str(round(price, 2)) +
                                ". Count at " + str(count)))
        buy(condition=True, buyAmount=FAST_DAY_MAX_BUYS)
    else:
        buy(condition=False)
    # if price >= MATwo >= EMATen >= EMAFifteen \
    #         and RSITwo > 55 \
    #         and lastTime > 2.0 \
    #         and count < FAST_DAY_MAX_BUYS \
    #         and price <= twentyPercentAboveOneHour \
    #         or price >= twentyPercentAboveOneHour \
    #         and price >= MATwo >= EMATen >= EMAFifteen \
    #         and count < FAST_DAY_MAX_BUYS \
    #         and lastTime > 15.00 \
    #         or price <= twentyPercentBelowOneHour \
    #         and count >= FAST_DAY_MAX_BUYS \
    #         and price <= MATwo >= EMAFive \
    #         and lastTime > 5.00:
    #
    #     updateMessageData(text=("FAST: Condition met to buy for the price of $"
    #                             + str(round((price + TRADING_BUFFER), 2)) +
    #                             ". Count at " + str(count)))
    #     buy(condition=True, buyAmount=FAST_DAY_MAX_BUYS)
    # else:
    #     buy(condition=False)

    # FAST: Selling conditions
    if price > lastBoughtPrice > 1.1 \
            and price > (EMAThirty + standardDeviation) \
            and count > 0 \
            and lastTime > 3.0:
        updateMessageData(text=("FAST: Condition met to sell for the price of $"
                                + str(round(price, 2)) +
                                ". Count at " + str(count)))
        sell(condition=True, sellAmount=FAST_DAY_MAX_BUYS)
    else:
        sell(condition=False)


# Checks to see if the prices meet the slow day conditions to buy or sell. Currently Extreme day conditions are
# prices that are greater than $1 but less than $2.50 moving averages in 1 hour.
def slowDay():
    global boughtInData, count, messageData, boughtDataOld
    price = pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]
    if boughtInData.empty:
        lastBoughtPrice = 0.0
        lastTime = 1.0
    else:
        lastBoughtPrice = (boughtDataOld['Price'].tail(count).mean() + 0.30)
        count = boughtInData.iloc[-1]['Count']

        # Get last execution time
        lastExec = boughtInData.iloc[-1]['exec_time']
        lastTime = getTimeToSec(time=lastExec)

    EMAThirty = pricesAndAverages.getData().iloc[-1]["EMA-30"]
    EMASixty = pricesAndAverages.getData().iloc[-1]["EMA-60"]
    standardDeviation = (round(float(numpy.std(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3))

    # SLOW: Buying conditions
    if price < (EMAThirty - standardDeviation) \
            and price < EMAThirty < EMASixty \
            and count < SLOW_DAY_MAX_BUYS \
            and lastTime > 5.0:
        updateMessageData(text=("SLOW1: Condition met to buy for the price of $"
                                + str(round(price, 2))
                                + ". Count at " + str(count)))
        buy(condition=True)
    else:
        buy(condition=False)

    # SLOW: Selling conditions
    if price > lastBoughtPrice > 1.1 \
            and price > (EMAThirty + standardDeviation) \
            and lastTime > 5.0 \
            and count > 0:
        updateMessageData(text=("SLOW: Condition met to sell for the price of $"
                                + str(round(price, 2))
                                + ". Count at " + str(count)))
        sell(condition=True, sellAmount=SLOW_DAY_MAX_BUYS)
    else:
        sell(condition=False)


# Checks to see if the prices meet the fast day conditions to buy or sell. Currently Extreme day conditions are
# prices that are greater than $0 but less than $1 moving averages in 1 hour.
def turtleDay():
    global boughtInData, count, messageData, boughtDataOld
    price = pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]
    if boughtInData.empty:
        profitCheck = 0.0
        lastBoughtPrice = 0.0
        lastSoldPrice = 0.0
        sellCheck = False
        lastTime = 1.0
    else:
        profitCheck = (boughtInData["Total"].sum())
        lastBoughtPrice = (boughtDataOld['Price'].tail(count).max() + 0.30)
        count = boughtInData.iloc[-1]['Count']

        # Get last execution time
        lastExec = boughtInData.iloc[-1]['exec_time']
        lastTime = getTimeToSec(time=lastExec)

        # If false, I'm either losing money or bought before I sold.
        futureProfit = (-price * 0.5) + profitCheck
        if profitCheck < 0:
            if futureProfit < profitCheck:
                sellCheck = True
            else:
                sellCheck = False
        else:
            sellCheck = False

    EMATen = pricesAndAverages.getData().iloc[-1]["EMA-10"]
    EMAFive = pricesAndAverages.getData().iloc[-1]["EMA-5"]
    EMAFifteen = pricesAndAverages.getData().iloc[-1]["EMA-15"]
    EMAThirty = pricesAndAverages.getData().iloc[-1]["EMA-30"]
    EMASixty = pricesAndAverages.getData().iloc[-1]["EMA-60"]
    RSIFifteen = pricesAndAverages.getData().iloc[-1]["RSI-15"]
    RSITen = pricesAndAverages.getData().iloc[-1]["RSI-10"]
    RSITwo = pricesAndAverages.getData().iloc[-1]["RSI-2"]
    MAFive = pricesAndAverages.getData().iloc[-1]["MA-5"]
    MATen = pricesAndAverages.getData().iloc[-1]["MA-10"]
    MATwo = pricesAndAverages.getData().iloc[-1]["MA-2"]
    twentyPercentBelowOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 20), 3)
    twentyPercentAboveOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 80), 3)
    standardDeviation = (round(float(numpy.std(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3))
    averagePrice = round(float(numpy.mean(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3)

    # TURTLE: Buying conditions
    if price < (averagePrice - standardDeviation) \
            and count < TURTLE_DAY_MAX_BUYS \
            and lastTime > 3.0:
        updateMessageData(text=("TURTLE: Condition met to buy for the price of $"
                                + str(round((price + TRADING_BUFFER), 2))
                                + ". Count at " + str(count)))
        buy(condition=True, buyAmount=TURTLE_DAY_MAX_BUYS)
    # if price > MATen > EMAFifteen > EMAThirty > EMASixty \
    #         and RSITen > 50 \
    #         and RSIFifteen > 50 \
    #         and count < TURTLE_DAY_MAX_BUYS \
    #         and price < twentyPercentAboveOneHour \
    #         and lastTime > 2.0\
    #         or price < MATwo < EMATen < EMAFifteen < EMAThirty\
    #         and count < TURTLE_DAY_MAX_BUYS \
    #         and price < EMASixty\
    #         and lastTime > 2.0:
    #     updateMessageData(text=("TURTLE: Condition met to buy for the price of $"
    #                             + str(round((price + TRADING_BUFFER), 2))
    #                             + ". Count at " + str(count)))
    #     buy(condition=True, buyAmount=TURTLE_DAY_MAX_BUYS)
    # # Try somewhat easy test if price is below the 20% below price. Buy in while it's down right before it goes up.(try)
    # elif twentyPercentBelowOneHour >= MAFive >= EMATen >= price \
    #         and count > TURTLE_DAY_MAX_BUYS \
    #         and lastTime > 2.0:
    #     updateMessageData(text=("TURTLE: Condition met to buy for the price of $"
    #                             + str(round((price + TRADING_BUFFER), 2))
    #                             + ". Count at " + str(count)))
    #     buy(condition=True)
    # # If price is down $4 from original bought price. Buy in on the lows when it couldn't sell.
    # elif price < (lastBoughtPrice - 4.0)\
    #         and count < SLOW_DAY_MAX_BUYS \
    #         and lastTime > 20.0\
    #         or price < (lastBoughtPrice - 4.0)\
    #         and count >= SLOW_DAY_MAX_BUYS\
    #         and lastTime > 50.0:
    #     updateMessageData(text=("SLOW: Condition met to buy for the price of $"
    #                             + str(round((price + TRADING_BUFFER), 2))
    #                             + ". Count at " + str(count)))
    #     buy(condition=True, buyAmount=SLOW_DAY_MAX_BUYS)
    else:
        buy(condition=False)

    # TURTLE: Selling conditions
    if price > (averagePrice + standardDeviation) \
            and price > lastBoughtPrice > 1.1 \
            and count > 0 \
            and lastTime > 3.0:
        updateMessageData(text=("TURTLE: Condition met to sell for the price of $"
                                + str(round(price, 2))
                                + ". Count at " + str(count)))
        sell(condition=True, sellAmount=TURTLE_DAY_MAX_BUYS)
    # if sellCheck == True \
    #         and price > lastBoughtPrice > 1.1 \
    #         and MATen < EMAFifteen < EMAThirty < EMASixty \
    #         and lastTime > 2.0\
    #         and count > 0\
    #         or price > MATwo > EMAFive \
    #         and price > lastBoughtPrice \
    #         and sellCheck == True \
    #         and RSITen > 50 \
    #         and RSIFifteen > 50 \
    #         and lastTime > 2.0\
    #         and count > 0:
    #     updateMessageData(text=("TURTLE: Condition met to sell for the price of $"
    #                             + str(round(price, 2))
    #                             + ". Count at " + str(count)))
    #     sell(condition=True, sellAmount=TURTLE_DAY_MAX_BUYS)
    # elif sellCheck == False \
    #         and price > lastBoughtPrice \
    #         and RSITwo > 50 \
    #         and RSITen > 50 \
    #         and RSIFifteen > 50 \
    #         and lastTime > 2.0\
    #         and count > 0:
    #     updateMessageData(text=("TURTLE: Condition met to sell for the price of $"
    #                             + str(round(price, 2))
    #                             + ". Count at " + str(count)))
    #     sell(condition=True, sellAmount=TURTLE_DAY_MAX_BUYS)
    else:
        sell(condition=False)


# This method will buy the desired amount of coins from RobinHood if the conditions are met.
def buy(condition=False, buyAmount=5, forceBuy=False):
    if not condition:
        return
    global count, boughtInData, messageData

    profit = (boughtInData["Total"].sum())
    availableCash = getCash()
    prices = pricesAndAverages.getPrices(coin=CRYPTO_CHOICE)

    price = round(float(prices['ask_price']), 2)

    if (price * MAX_BUY_AND_SELL_LIMIT) <= availableCash:
        coins = MAX_BUY_AND_SELL_LIMIT
    elif (price * MIN_BUY_AND_SELL_LIMIT) <= availableCash:
        coins = MIN_BUY_AND_SELL_LIMIT
    else:
        updateMessageData(text="Not enough buying power")
        return

    if not forceBuy:
        try:
            robin_stocks.robinhood.order_buy_crypto_by_quantity(CRYPTO_CHOICE, coins)
            count = count + 1
            updateBoughtData(price=price, total=(price * coins), coin_count=coins, profit=profit, count=count)
            updateBoughtDataOld(price=price)
            updateMessageData(text=("Bought in at $" + str(price) + ", " + str(coins) + " (coins)" +
                                    ". Count at " + str(count) + " times at " + str(datetime.datetime.now())))
        except:
            updateMessageData(text="EXCEPTION AT BUY METHOD.")
        return
    else:
        try:
            robin_stocks.robinhood.order_buy_crypto_by_quantity(CRYPTO_CHOICE, coins)
            count = count + 1
            updateBoughtData(price=price, total=(price * coins), coin_count=coins, profit=profit, count=count)
            updateBoughtDataOld(price=price)
            updateMessageData(text=("Bought in at $" + str(price) + ", " + str(coins) + " (coins)" +
                                    ". Count at " + str(count) + " times at " + str(datetime.datetime.now())))
        except:
            updateMessageData(text="EXCEPTION AT BUY METHOD.")
        return


# This method will get the amount of cash that you have available in RobinHood
def getCash():
    global messageData
    reserve = RESERVE_CASH_LIMIT
    try:
        me = robin_stocks.robinhood.account.load_phoenix_account(info=None)
        cash = float(me['crypto_buying_power']['amount'])
    except:
        updateMessageData(text="An exception occurred getting cash amount.")
        return -1.0
    if cash < reserve:
        updateMessageData(text=("Your reserve amount is $" +
                                str(reserve) + ". You need more to buy."))
        return 0.0
    else:
        return cash - reserve


# This method will sell the desired amount of coins from RobinHood if the conditions are met.
def sell(condition=False, sellAmount=5):
    global count, soldData, messageData, boughtInData

    if not condition:
        return
    if count <= 0:
        return

    coinHeld = boughtInData["Coin_Count"].tail(count).sum()

    price = round((pricesAndAverages.getData().iloc[-1][CRYPTO_CHOICE]), 2)
    profit = (boughtInData["Total"].sum() + (-price * coinHeld))

    try:
        results = robin_stocks.robinhood.order_sell_crypto_by_quantity(CRYPTO_CHOICE, coinHeld)
        count = 0
        updateBoughtData(price=price, total=(-price * coinHeld), coin_count=coinHeld, profit=profit, count=count)
        updateMessageData(("Sold at a price of $" + str(price) + "  " + str(coinHeld)
                           + " (coins) at " + str(datetime.datetime.now())))
        print("Results: " + results)
    except:
        updateMessageData("EXCEPTION AT SELLING")
        return


# This is a unused method that I had earlier. May use it in the future tho. It updates everytime I sell with the value
# that the coin was sold at.
def updateSoldData(sold_check=False, sold_value=0.0, count=0):
    global soldData
    rowData = {}
    rowData.update({'exec_time': datetime.datetime.now(),
                    'Sold_Check': sold_check, 'Sold_Value': sold_value, 'Count': count})
    soldData = soldData.append(rowData, ignore_index=True)
    soldData.to_pickle('soldData.pickle')


# This method updates everytime the program buys in RobinHood. It will keep record or the price, profit, and amount of
# coins bought.
def updateBoughtData(price=0.0, total=0.0, coin_count=0.0, profit=0, count=0):
    global boughtInData
    rowData = {}
    rowData.update({'exec_time': datetime.datetime.now(), 'Price': price,
                    'Coin_Count': coin_count, 'Total': total, 'Profit': profit, 'Count': count})
    boughtInData = boughtInData.append(rowData, ignore_index=True)
    boughtInData.to_pickle('boughtIn.pickle')


# This is another method I had to create so I could keep track of how many times it bought vs. sold.
def updateBoughtDataOld(price=0.0):
    global boughtDataOld
    rowData = {}
    rowData.update({'exec_time': datetime.datetime.now(), 'Price': price})
    boughtDataOld = boughtDataOld.append(rowData, ignore_index=True)
    boughtDataOld.to_pickle('boughtInOld.pickle')


# This method is used to update the message data frame that shows each time it has bought in on the UI.
def updateMessageData(text=""):
    global messageData
    rowData = {}
    rowData.update({'exec_time': datetime.datetime.now(),
                    'Messages': text})
    messageData = messageData.append(rowData, ignore_index=True)
    messageData.to_pickle('messages.pickle')


# This method gets and returns a certain amount of time to seconds.
def getTimeToSec(time=""):
    now = datetime.datetime.now()
    duration = now - time
    durationInSec = duration.total_seconds()
    return divmod(durationInSec, 60)[0]


# Returns the sold data frame.
def getSoldData():
    global soldData
    return soldData


# Returns the bought data frame.
def getBoughtData():
    global boughtInData
    return boughtInData


# Returns the old bought data frame.
def getBoughtDataOld():
    global boughtDataOld
    return boughtDataOld


# returns the messages data frame.
def getMessageData():
    global messageData
    return messageData


# Loads the old bought in data frame from a pickle file and creates one if there isn't one.
def loadBoughtInDataOld():
    global boughtDataOld
    if path.exists('boughtInOld.pickle'):
        boughtDataOld = pd.read_pickle('boughtInOld.pickle')
    else:
        column_names = ['exec_time', 'Price']
        boughtDataOld = pd.DataFrame(columns=column_names)
        boughtDataOld.style.set_properties(**{'text-align': 'left'})
        file = open('boughtInOld.pickle', 'wb')
        pickle.dump(boughtDataOld, file)
        file.close()


# Loads the bought in data frame from a pickle file and creates one if there isn't one.
def loadBoughtInDataFrame():
    global boughtInData
    pd.set_option('max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    if path.exists("boughtIn.pickle"):
        boughtInData = pd.read_pickle('boughtIn.pickle')
        # boughtInData['Count'] = boughtInData['Count'].astype(int)
        # boughtInData.replace({'Count': {-1: 0}}, inplace=True)
        # boughtInData.iloc[-1, boughtInData.columns.get_loc('Count')] = 1
        # boughtInData.to_pickle('boughtIn.pickle')
        # boughtInData = pd.read_pickle('boughtIn.pickle')
    else:
        column_names = ['exec_time', "Price", "Coin_Count", "Total", "Profit", "Count"]
        boughtInData = pd.DataFrame(columns=column_names)
        boughtInData.style.set_properties(**{'text-align': 'left'})
        file = open('boughtIn.pickle', 'wb')
        pickle.dump(boughtInData, file)
        file.close()
    return boughtInData


# Loads the messages data frame from a pickle file and creates one if there isn't one.
def loadStoredMessages():
    global messageData
    pd.set_option('max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    if path.exists("messages.pickle"):
        messageData = pd.read_pickle('messages.pickle')
        messageData.style.set_properties(**{'text-align': 'left'})
    else:
        column_names = ['exec_time', 'Messages']
        messageData = pd.DataFrame(columns=column_names)
        messageData.style.set_properties(**{'text-align': 'left'})
        file = open('messages.pickle', 'wb')
        pickle.dump(messageData, file)
        file.close()
    return boughtInData


# Loads the sold data frame from a pickle file and creates one if there isn't one.
def loadSoldDataFrame():
    global soldData
    pd.set_option('max_columns', None)
    pd.set_option('display.expand_frame_repr', False)
    if path.exists("soldData.pickle"):
        soldData = pd.read_pickle('soldData.pickle')
    else:
        column_names = ['exec_time', "Sold_Check", "Sold_Value", "Count"]
        soldData = pd.DataFrame(columns=column_names)
        file2 = open('soldData.pickle', 'wb')
        pickle.dump(soldData, file2)
        file2.close()
    return soldData


# method to hold trades when in-between fast and slow days as well as fast and extreme days.
def holdTrade():
    return
