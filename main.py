import datetime
import math
import time
from tkinter import *
import pandas as pd
import numpy
import robin_stocks.robinhood.account
import robin_stocks.robinhood.authentication as rb
from requests import HTTPError
import pricesAndAverages
import configurationFile
import sys
import tradingStrategies
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.figure import Figure
# import matplotlib.animation as animation
# from matplotlib import style

connection_timeout = 120
CRYPTO_CHOICE = configurationFile.config['COIN_CHOICE']

ONE_HOUR = configurationFile.config['ONE_HOUR']
TWO_HOUR = configurationFile.config['TWO_HOUR']
FOUR_HOUR = configurationFile.config['FOUR_HOUR']
SIX_HOUR = configurationFile.config['SIX_HOUR']
EIGHTEEN_HOUR = configurationFile.config['EIGHTEEN_HOUR']

UPDATE_PRICE_INTERVALS = configurationFile.config['UPDATE_PRICE_INTERVALS']

sys.setrecursionlimit(10 ** 6)


# This is the main method for the whole UI program basically. It runs every 10 min to update the graph,
# prices, run trades if the option is selected, updates messages, and updates bought in info. You can
# Change the time if you'd like, but right now I just prefer to run everything in 10 min intervals. It seems
# to work the best.
def updatePriceLabelTwoMin():
    global cryptoPriceLabel, price, ax
    start_time = time.time()
    while True:
        try:
            ETCWorth.config(text=format(float(robin_stocks.robinhood.account.load_phoenix_account()
                                              ['crypto']['equity']['amount']), '.2f'))
            prices = pricesAndAverages.getPrices(coin=CRYPTO_CHOICE)
            price = round(float(prices['bid_price']), 2)
            # buyPrice = round(float(prices['ask_price']), 2)
            # print("Difference: " + format((buyPrice - price), '.2f'))
            break
        except HTTPError as e:
            if e.code == 502:
                if time.time() > start_time + connection_timeout:
                    raise Exception('Unable to get updates after {} seconds of ConnectionErrors'.format(connection_timeout))
                else:
                    time.sleep(1)  # attempting once every second
                # Ok, I've got 'em. Let's iterate through each one
            return
    # start_time = time.time()
    # while True:
    #     try:
    #         ETCWorth.config(text=format(float(robin_stocks.robinhood.account.load_phoenix_account()
    #                                           ['crypto']['equity']['amount']), '.2f'))
    #         break
    #     except TypeError:
    #         if time.time() > start_time + connection_timeout:
    #             raise Exception('Unable to get updates after {} seconds of ConnectionErrors'.format(connection_timeout))
    #         else:
    #             time.sleep(1)  # attempting once every second
    #         # Ok, I've got 'em. Let's iterate through each one
    #         return

    cryptoPriceLabel.config(text=format(price, '.2f'))
    now = datetime.datetime.now()
    pricesAndAverages.updateDataframe(now, currentPrices=price)

    # twentyPercentBelowOneHour = (round(float(numpy.std(botFile.getData()["ETC"].tail(1080))), 3))
    # twentyPercentAboveOneHour = round(float(numpy.mean(botFile.getData()["ETC"].tail(1800))), 3)
    twentyPercentBelowOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 20), 3)
    # twentyPercentBelowOneHour = talib.LINEARREG_SLOPE(botFile.getData()["ETC"].values, timeperiod=1800)
    twentyPercentAboveOneHour = round(numpy.percentile(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR), 80), 3)
    twentyPercentBelow = (round(float(numpy.std(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3))
    # twentyPercentAbove = talib.TSF(botFile.getData()["ETC"].values, timeperiod=1800)
    twentyPercentAbove = round(float(numpy.mean(pricesAndAverages.getData()[CRYPTO_CHOICE].tail(ONE_HOUR))), 3)
    boughtInValue.config(text=tradingStrategies.getBoughtData().tail(6))
    # cashLabelValue.config(text=tradingStrategies.getSoldData().tail(4))
    messagesValue.config(text=tradingStrategies.getMessageData()['Messages'].tail(4))

    if math.isnan(pricesAndAverages.getData().iloc[-1]['EMA-60']):
        tradingColorLabel.config(bg='#F15443')
    else:
        tradingColorLabel.config(bg='#5CF143')
        if tradeOptionsVar.get() == 0:
            tradingStrategies.runTrades(run=False)
            tradingColorLabel.config(bg='#F15443')
            slowDayTrade.config(state=DISABLED)
            fastDayTrade.config(state=DISABLED)
            extremeDayTrade.config(state=DISABLED)
        elif tradeOptionsVar.get() == 1:
            tradingColorLabel.config(bg='#5CF143')
            tradingStrategies.runTrades(run=True)
            slowDayTrade.config(state=DISABLED)
            fastDayTrade.config(state=DISABLED)
            extremeDayTrade.config(state=DISABLED)
        elif tradeOptionsVar.get() == 2:
            slowDayTrade.config(state=ACTIVE, value=0)
            fastDayTrade.config(state=ACTIVE, value=1)
            extremeDayTrade.config(state=ACTIVE, value=2)
            tradingColorLabel.config(bg='#5CF143')
            if manualTradingOptionsVar == 0:
                tradingStrategies.slowDay()
            if manualTradingOptionsVar == 1:
                tradingStrategies.fastDay()
            if manualTradingOptionsVar == 2:
                tradingStrategies.extremeDay()
        count = tradingStrategies.getBoughtData().iloc[-1]['Count']
        if graphChoice.get() == 0:
            if 5.0 <= (twentyPercentAboveOneHour - twentyPercentBelowOneHour):
                averageBuy.config(text=format(tradingStrategies.getBoughtDataOld()['Price'].tail(count).max(), '.2f'))
                cryptoChoice.config(text="Extreme Day Trading (1 hour AVG)")
                graphExtremeAndFast1H()
            elif 4.50 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) < 5.0:
                cryptoChoice.config(text="Hold buys and sells... In-between fast and extreme day ( 1 hour AVG)",
                                    font="JetBrains 12 bold")
                graphExtremeAndFast1H()
            elif 2.5 <= (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 4.50:
                averageBuy.config(text=format(tradingStrategies.getBoughtDataOld()['Price'].tail(count).max(), '.2f'))
                cryptoChoice.config(text="Fast Day Trading (1 hour AVG)")
                graphExtremeAndFast1H()
            elif 2.0 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) < 2.5:
                cryptoChoice.config(text="Hold buys and sells... In-between fast and slow day (1 hour AVG)",
                                    font="JetBrains 12 bold")
                graphSlow1H()
            elif 1.0 < (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 2.0:
                averageBuy.config(text=format(tradingStrategies.getBoughtDataOld()['Price'].tail(count).max(), '.2f'))
                cryptoChoice.config(text="Slow Day Trading (1 hour AVG)")
                graphSlow1H()
            elif (twentyPercentAboveOneHour - twentyPercentBelowOneHour) <= 1.0:
                averageBuy.config(text=format(tradingStrategies.getBoughtDataOld()['Price'].tail(count).max(), '.2f'))
                cryptoChoice.config(text="Turtle Day Trading (1 hour AVG)")
                graphSlow1H()
            else:
                tradingColorLabel.config(bg='#F15443')
        elif graphChoice.get() == 1:
            graphOptions(graphTime=ONE_HOUR, text="ETC Graph for Slow Day | 1 Hour")
        elif graphChoice.get() == 2:
            graphOptions(graphTime=TWO_HOUR, text="ETC Graph for Slow Day | 2 Hour")
        elif graphChoice.get() == 3:
            graphOptions(graphTime=FOUR_HOUR, text="ETC Graph for Slow Day | 4 Hour")
        elif graphChoice.get() == 4:
            graphOptions(graphTime=SIX_HOUR, text="ETC Graph for Slow Day | 6 Hour")
        elif graphChoice.get() == 5:
            graphOptions(graphTime=EIGHTEEN_HOUR, text="ETC Graph for Slow Day | 18 Hour")
        elif graphChoice.get() == 7:
            graphOptionsF(graphTime=ONE_HOUR, text="ETC Graph for Fast Day | 1 Hour")
        elif graphChoice.get() == 8:
            graphOptionsF(graphTime=TWO_HOUR, text="ETC Graph for Fast Day | 2 Hour")
        elif graphChoice.get() == 9:
            graphOptionsF(graphTime=FOUR_HOUR, text="ETC Graph for Fast Day | 4 Hour")
        elif graphChoice.get() == 10:
            graphOptionsF(graphTime=SIX_HOUR, text="ETC Graph for Fast Day | 6 Hour")
        elif graphChoice.get() == 11:
            graphOptionsF(graphTime=EIGHTEEN_HOUR, text="ETC Graph for Fast Day | 18 Hour")
    # EMATwo.config(text=str(format(botFile.getEMATwo(), '.2f')))
    # RSITwo.config(text=str(format(botFile.getRSITwo(), '.2f')))
    # MATwo.config(text=str(format(botFile.getMATwo(), '.2f')))
    #
    # EMAFive.config(text=str(format(botFile.getEMAFive(), '.2f')))
    # RSIFive.config(text=str(format(botFile.getRSIFive(), '.2f')))
    # MAFive.config(text=str(format(botFile.getMAFive(), '.2f')))
    #
    # EMATen.config(text=str(format(botFile.getEMATen(), '.2f')))
    # RSITen.config(text=str(format(botFile.getRSITen(), '.2f')))
    # MATen.config(text=str(format(botFile.getMATen(), '.2f')))
    #
    # EMAFifteen.config(text=str(format(botFile.getEMAFifteen(), '.2f')))
    # RSIFifteen.config(text=str(format(botFile.getRSIFifteen(), '.2f')))
    # MAFifteen.config(text=str(format(botFile.getMAFifteen(), '.2f')))
    #
    # EMAThirty.config(text=str(format(botFile.getEMAThirty(), '.2f')))
    # RSIThirty.config(text=str(format(botFile.getRSIThirty(), '.2f')))
    # MAThirty.config(text=str(format(botFile.getMAThirty(), '.2f')))
    #
    # EMASixty.config(text=str(format(botFile.getEMASixty(), '.2f')))
    # RSISixty.config(text=str(format(botFile.getRSISixty(), '.2f')))
    # MASixty.config(text=str(format(botFile.getMASixty(), '.2f')))

    twentyAbove1.config(text=twentyPercentAboveOneHour)
    twentyBelow1.config(text=twentyPercentBelowOneHour)
    twentyAbove2.config(text=twentyPercentAbove)
    twentyBelow2.config(text=twentyPercentBelow)

    # 600000 is milliseconds for 10 min.
    root.after(UPDATE_PRICE_INTERVALS, updatePriceLabelTwoMin)


# def updateCashLabel(text=" "):
#     cashLabelValue.config(text=text)


# def tradingOptions():
#     if tradeOptionsVar.get() == 0:
#         slowDayTrade.config(state=DISABLED)
#         fastDayTrade.config(state=DISABLED)
#         extremeDayTrade.config(state=DISABLED)
#         tradingColorLabel.config(bg='#F15443')
#         return
#     if tradeOptionsVar.get() == 2:
#         slowDayTrade.config(state=ACTIVE, value=0, command=manualTradingOptions)
#         fastDayTrade.config(state=ACTIVE, value=1, command=manualTradingOptions)
#         extremeDayTrade.config(state=ACTIVE, value=2, command=manualTradingOptions)
#         tradingColorLabel.config(bg='#5CF143')
#     elif tradeOptionsVar.get() == 1:
#         slowDayTrade.config(state=DISABLED)
#         fastDayTrade.config(state=DISABLED)
#         extremeDayTrade.config(state=DISABLED)
#         tradingColorLabel.config(bg='#5CF143')
#
#
# def manualTradingOptions():
#     if manualTradingOptionsVar.get() == 0:
#         print("Hui")
#         runSlowDay()


# GUI Interface loop.
# Program start configs
root = Tk()
root.title('Crypto Bot')
root.geometry("1500x1000")
root.config(bg='#504D4C')
photo = PhotoImage(file='botBit24.png')
root.iconphoto(False, photo)
getData = pricesAndAverages.loadDataframe()
tradingStrategies.loadBoughtInDataFrame()
tradingStrategies.loadSoldDataFrame()
tradingStrategies.loadStoredMessages()
tradingStrategies.loadBoughtInDataOld()
pd.set_option('max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', None)

userName = configurationFile.rh["username"]
passWord = configurationFile.rh["password"]
time_logged_in = 60 * 60 * 60 * 7
rb.login(username=userName,
         password=passWord,
         expiresIn=time_logged_in,
         scope='internal',
         by_sms=True,
         store_session=True)

# Graph configuration
figure = plt.Figure(figsize=(15, 5), dpi=100)
figure.patch.set_facecolor('#504D4C')
ax = figure.add_subplot(111)
ax.set_facecolor('#504D4C')
graph = FigureCanvasTkAgg(figure, master=root)
graph.get_tk_widget().grid(row=16, rowspan=15, column=1, columnspan=20, sticky='W')


def graphExtremeAndFast1H():
    graphTime = ONE_HOUR
    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x4 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x4, label='EMA-10')
    ax.plot(y, x6, label='EMA-30')
    ax.legend()
    ax.set_title(CRYPTO_CHOICE + ' Graph for Fast Day | 1 Hour AVG')
    ax.grid()
    graph.draw()


def graphExtremeAndFast2H():
    graphTime = TWO_HOUR

    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x4 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x4, label='EMA-10')
    ax.plot(y, x6, label='EMA-30')
    ax.legend()
    ax.set_title(CRYPTO_CHOICE + ' Graph for Fast Day | 2 Hour AVG')
    ax.grid()
    graph.draw()


def graphSlow1H():
    graphTime = ONE_HOUR

    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x3 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x5 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-60'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x3, label='EMA-10')
    ax.plot(y, x5, label='EMA-30')
    ax.plot(y, x6, label='EMA-60')
    ax.legend()
    ax.set_title(CRYPTO_CHOICE + ' Graph for Slow Day | 1 Hour AVG')
    ax.grid()
    graph.draw()


def graphSlow2H():
    graphTime = TWO_HOUR

    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x3 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x5 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-60'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x3, label='EMA-10')
    ax.plot(y, x5, label='EMA-30')
    ax.plot(y, x6, label='EMA-60')
    ax.legend()
    ax.set_title(CRYPTO_CHOICE + ' Graph for Slow Day | 2 Hour AVG')
    ax.grid()
    graph.draw()


def graphOptions(graphTime=ONE_HOUR, text=" "):
    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x3 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x5 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-60'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x3, label='EMA-10')
    ax.plot(y, x5, label='EMA-30')
    ax.plot(y, x6, label='EMA-60')
    ax.legend()
    ax.set_title(text)
    ax.grid()
    graph.draw()


def graphOptionsF(graphTime=ONE_HOUR, text=" "):
    global ax, y, x1, x2, x3, x4, x5, x6
    y = pricesAndAverages.getData()['exec_time'].tail(graphTime)
    x1 = pricesAndAverages.getData()[CRYPTO_CHOICE].tail(graphTime)
    x4 = pricesAndAverages.getData()['EMA-10'].tail(graphTime)
    x6 = pricesAndAverages.getData()['EMA-30'].tail(graphTime)
    ax.clear()
    ax.plot(y, x1, label=CRYPTO_CHOICE)
    ax.plot(y, x4, label='EMA-10')
    ax.plot(y, x6, label='EMA-30')
    ax.legend()
    ax.set_title(text)
    ax.grid()
    graph.draw()


def deleteRow():
    count = tradingStrategies.getBoughtData().iloc[-1]['Count']
    boughtData = tradingStrategies.getBoughtData()
    boughtData = boughtData.drop(labels=int(textInput.get()), axis=0)
    boughtData.to_pickle("boughtIn.pickle")
    tradingStrategies.loadBoughtInDataFrame()
    averageBuy.config(text=tradingStrategies.getBoughtDataOld()['Price'].tail(count).mean())


def buyCoin():
    tradingStrategies.buy(condition=True, forceBuy=True)


# Delete Button
textInput = StringVar()
deleteOption = Entry(root, width=20, textvariable=textInput)
deleteOption.grid(row=15, column=1, sticky='W')
button = Button(root, text='DELETE', command=deleteRow)
button.grid(row=15, column=0, sticky='W')
averageBuy = Label(root, text="    ")
averageBuy.grid(row=15, column=2, sticky='W')
ETCWorth = Label(root, text=" ")
ETCWorth.grid(row=16, column=2, sticky='W')

# buyInput = StringVar()
# buyAmount = Entry(root, width=20, textvariable=buyInput)
# buyAmount.grid(row=16, column=2, sticky='W')
buyButton = Button(root, text='Buy 1 Coin', command=buyCoin)
buyButton.grid(row=16, column=0, sticky='W')

global price
price = pricesAndAverages.getPrices(coin="ETC")
print(getData.tail())

global cryptoPriceLabel
cryptoChoice = Label(root, text="Current crypto being traded:",
                     font="JetBrains 17 bold", bg='#504D4C')
cryptoChoice.grid(row=0, column=0, columnspan=3, sticky='W')
cryptoNameLabel = Label(root, text=CRYPTO_CHOICE, font="JetBrains 15 bold", bg='#504D4C').grid(row=1, column=0, sticky='W')
cryptoPriceLabel = Label(root, text=price, font="JetBrains 13", bg='#504D4C')
cryptoPriceLabel.grid(row=2, column=0, sticky='W')

# Above and Below AVG's
twentyAbove2Title = Label(root, text="20% Above 2H:", font="JetBrains 15 bold", bg='#504D4C')
twentyAbove2Title.grid(row=1, column=8)
twentyBelow2Title = Label(root, text="20% Below 2H:", font="JetBrains 15 bold", bg='#504D4C')
twentyBelow2Title.grid(row=1, column=9)
twentyAbove1Title = Label(root, text="20% Above 1H:", font="JetBrains 15 bold", bg='#504D4C')
twentyAbove1Title.grid(row=1, column=6)
twentyBelow1Title = Label(root, text="20% Below 1H:", font="JetBrains 15 bold", bg='#504D4C')
twentyBelow1Title.grid(row=1, column=7)

twentyAbove1 = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
twentyAbove1.grid(row=2, column=6)
twentyBelow1 = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
twentyBelow1.grid(row=2, column=7)
twentyAbove2 = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
twentyAbove2.grid(row=2, column=8)
twentyBelow2 = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
twentyBelow2.grid(row=2, column=9)

# EMATwo = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMATwo.grid(row=1, column=4)
# EMAFive = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMAFive.grid(row=1, column=5)
# EMATen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMATen.grid(row=1, column=6)
# EMAFifteen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMAFifteen.grid(row=1, column=7)
# EMAThirty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMAThirty.grid(row=1, column=8)
# EMASixty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# EMASixty.grid(row=1, column=9)

# EMATwoTitle = Label(root, text=" EMA-2:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMATwoTitle.grid(row=0, column=4)
# EMAFiveTitle = Label(root, text=" EMA-5:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMAFiveTitle.grid(row=0, column=5)
# EMATenTitle = Label(root, text=" EMA-10:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMATenTitle.grid(row=0, column=6)
# EMAFifteenTitle = Label(root, text=" EMA-15:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMAFifteenTitle.grid(row=0, column=7)
# EMAThirtyTitle = Label(root, text=" EMA-30:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMAThirtyTitle.grid(row=0, column=8)
# EMASixtyTitle = Label(root, text=" EMA-60:  ", font="JetBrains 16 bold", bg='#504D4C')
# EMASixtyTitle.grid(row=0, column=9)

# ------------

# RSITwo = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSITwo.grid(row=3, column=4)
# RSIFive = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSIFive.grid(row=3, column=5)
# RSITen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSITen.grid(row=3, column=6)
# RSIFifteen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSIFifteen.grid(row=3, column=7)
# RSIThirty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSIThirty.grid(row=3, column=8)
# RSISixty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# RSISixty.grid(row=3, column=9)

# RSITwoTitle = Label(root, text=" RSI-2:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSITwoTitle.grid(row=2, column=4)
# RSIFiveTitle = Label(root, text=" RSI-5:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSIFiveTitle.grid(row=2, column=5)
# RSITenTitle = Label(root, text=" RSI-10:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSITenTitle.grid(row=2, column=6)
# RSIFifteenTitle = Label(root, text=" RSI-15:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSIFifteenTitle.grid(row=2, column=7)
# RSIThirtyTitle = Label(root, text=" RSI-30:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSIThirtyTitle.grid(row=2, column=8)
# RSISixtyTitle = Label(root, text=" RSI-60:  ", font="JetBrains 16 bold", bg='#504D4C')
# RSISixtyTitle.grid(row=2, column=9)

# ------------

# MATwo = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MATwo.grid(row=5, column=4)
# MAFive = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MAFive.grid(row=5, column=5)
# MATen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MATen.grid(row=5, column=6)
# MAFifteen = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MAFifteen.grid(row=5, column=7)
# MAThirty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MAThirty.grid(row=5, column=8)
# MASixty = Label(root, text=" ", font="JetBrains 13", bg='#504D4C')
# MASixty.grid(row=5, column=9)

# MATwoTitle = Label(root, text=" MA-2:  ", font="JetBrains 16 bold", bg='#504D4C')
# MATwoTitle.grid(row=4, column=4)
# MAFiveTitle = Label(root, text=" MA-5:  ", font="JetBrains 16 bold", bg='#504D4C')
# MAFiveTitle.grid(row=4, column=5)
# MATenTitle = Label(root, text=" MA-10:  ", font="JetBrains 16 bold", bg='#504D4C')
# MATenTitle.grid(row=4, column=6)
# MAFifteenTitle = Label(root, text=" MA-15:  ", font="JetBrains 16 bold", bg='#504D4C')
# MAFifteenTitle.grid(row=4, column=7)
# MAThirtyTitle = Label(root, text=" MA-30:  ", font="JetBrains 16 bold", bg='#504D4C')
# MAThirtyTitle.grid(row=4, column=8)
# MASixtyTitle = Label(root, text=" MA-60:  ", font="JetBrains 16 bold", bg='#504D4C')
# MASixtyTitle.grid(row=4, column=9)

# ------------

# BoughtIn Labels
boughtIn = Label(root, text='Bought in Info:', font="JetBrains 13 bold", bg='#504D4C')
boughtIn.grid(row=4, column=4, columnspan=5, sticky='W')
boughtInValue = Label(root, text=" ", bg='#504D4C', font="JetBrains 10")
boughtInValue.grid(row=5, rowspan=5, column=4, columnspan=10, sticky='NW')

# cashLabel = Label(root, text="Sold Info: ", font="JetBrains 13 bold", bg='#504D4C')
# cashLabel.grid(row=8, column=4, columnspan=5, sticky='W')
# cashLabelValue = Label(root, text=" ", bg='#504D4C', font="JetBrains 10")
# cashLabelValue.grid(row=9, rowspan=5, column=4, columnspan=5, sticky='W')

# columns = ('#4', '#5')
# tree = ttk.Treeview(root, columns=columns, show='headings')
# tree.heading('#4', text='Execution Time')
# tree.heading('#5', text='Messages')
# tree.insert('', Tk().END, values=tradingStrategies.getMessageData().tail(5))
# tree.grid(row=14, column=4, columnspan=10, sticky='NW')

messagesLabelTitle = Label(root, text="Messages: ", font="JetBrains 13 bold", bg='#504D4C')
messagesLabelTitle.grid(row=10, column=4, columnspan=10, sticky='NW')
messagesValue = Label(root, text=" ", bg='#504D4C', font="JetBrains 10")
messagesValue.grid(row=11, rowspan=5, column=4, columnspan=10, sticky='NW')

tradingColorLabel = Label(root, text="         ", bg='#F15443')
tradingColorLabel.grid(row=5, column=0, sticky='W')
tradingOptionLabel = Label(root, text="Trading:", font="JetBrains 10", bg='#504D4C')
tradingOptionLabel.grid(row=4, column=0, sticky='NW')

# Trading Options
tradeOptionsVar = IntVar()
manualTradingOptionsVar = IntVar()

tradesDisabled = Radiobutton(root, text='Trades Off',
                             variable=tradeOptionsVar, font="JetBrains 13",
                             value=0, bg='#504D4C')
tradesDisabled.grid(row=6, column=0, columnspan=3, sticky='W')
enableAutoTrades = Radiobutton(root, text='Auto Trades (recommended)',
                               variable=tradeOptionsVar, font="JetBrains 13",
                               value=1, bg='#504D4C')
enableAutoTrades.grid(row=7, column=0, columnspan=3, sticky='W')
enableTradesRadio = Radiobutton(root, text='Manual Trades',
                                variable=tradeOptionsVar, font="JetBrains 13",
                                value=2, bg='#504D4C')
enableTradesRadio.grid(row=8, column=0, columnspan=3, sticky='W')

# Manual Trading Options
slowDayTrade = Radiobutton(root, text='Slow Day (Highs and lows smaller than $2)',
                           variable=manualTradingOptionsVar, font="JetBrains 10", state=DISABLED, bg='#504D4C')
slowDayTrade.grid(row=9, column=0, columnspan=4, sticky='W')
fastDayTrade = Radiobutton(root, text='Fast Day (Highs and lows between $2.50 and $4.50)',
                           variable=manualTradingOptionsVar, font="JetBrains 10", state=DISABLED, bg='#504D4C')
fastDayTrade.grid(row=10, column=0, columnspan=4, sticky='W')
extremeDayTrade = Radiobutton(root, text='Extreme Day (Highs and lows greater than $5)',
                              variable=manualTradingOptionsVar, font="JetBrains 10", state=DISABLED, bg='#504D4C')
extremeDayTrade.grid(row=11, column=0, columnspan=4, sticky='W')

# Graph Slow Day Options
graphLabel = Label(root, text="Graph  O", font="JetBrains 13 bold", bg='#504D4C')
graphLabel.grid(row=17, column=0, columnspan=2, sticky='W')
graphChoice = IntVar()
graphAuto = Radiobutton(root, text='Auto', font="JetBrains 10", variable=graphChoice,
                        value=0, bg='#504D4C')
graphAuto.grid(row=18, column=0, sticky='W')
graph1Hour = Radiobutton(root, text='1 Hour', font="JetBrains 10", variable=graphChoice,
                         value=1, bg='#504D4C')
graph1Hour.grid(row=19, column=0, sticky='W')
graph2Hour = Radiobutton(root, text='2 Hour', font="JetBrains 10", variable=graphChoice,
                         value=2, bg='#504D4C')
graph2Hour.grid(row=20, column=0, sticky='W')
graph4Hour = Radiobutton(root, text='4 Hour', font="JetBrains 10", variable=graphChoice,
                         value=3, bg='#504D4C')
graph4Hour.grid(row=21, column=0, sticky='W')
graph6Hour = Radiobutton(root, text='6 Hour', font="JetBrains 10", variable=graphChoice,
                         value=4, bg='#504D4C')
graph6Hour.grid(row=22, column=0, sticky='W')
graph18Hour = Radiobutton(root, text='18 Hour', font="JetBrains 10", variable=graphChoice,
                          value=5, bg='#504D4C')
graph18Hour.grid(row=23, column=0, sticky='W')

# Graph Fast Day Options
graphLabelF = Label(root, text="ptions: ", font="JetBrains 13 bold", bg='#504D4C')
graphLabelF.grid(row=17, column=1, columnspan=2, sticky='W')
graphChoiceF = IntVar()
graphAutoF = Radiobutton(root, text='Auto', font="JetBrains 10", variable=graphChoice,
                         value=12, bg='#504D4C')
graphAutoF.grid(row=18, column=1, sticky='W')
graph1HourF = Radiobutton(root, text='1 Hour F', font="JetBrains 10", variable=graphChoice,
                          value=7, bg='#504D4C')
graph1HourF.grid(row=19, column=1, sticky='W')
graph2HourF = Radiobutton(root, text='2 Hour F', font="JetBrains 10", variable=graphChoice,
                          value=8, bg='#504D4C')
graph2HourF.grid(row=20, column=1, sticky='W')
graph4HourF = Radiobutton(root, text='4 Hour F', font="JetBrains 10", variable=graphChoice,
                          value=9, bg='#504D4C')
graph4HourF.grid(row=21, column=1, sticky='W')
graph6HourF = Radiobutton(root, text='6 Hour F', font="JetBrains 10", variable=graphChoice,
                          value=10, bg='#504D4C')
graph6HourF.grid(row=22, column=1, sticky='W')
graph18HourF = Radiobutton(root, text='18 Hour F', font="JetBrains 10", variable=graphChoice,
                           value=11, bg='#504D4C')
graph18HourF.grid(row=23, column=1, sticky='W')

#

# c2 = Checkbutton(root, text=' RSI(2)', variable=checkBoxRSITwo, onvalue=1, offvalue=0, font="Helvetica")
# c2.grid(row=5, column=0)
# c3 = Checkbutton(root, text=' MA(2)', variable=checkBoxMATwo, onvalue=1, offvalue=0, font="Helvetica")
# c3.grid(row=6, column=0)
#
# checkBoxEMAFive = IntVar()
# checkBoxRSIFive = IntVar()
# checkBoxMAFive = IntVar()
#
# c4 = Checkbutton(root, text=" EMA(5)", variable=checkBoxEMAFive, onvalue=1, offvalue=0, font="Helvetica")
# c4.grid(row=7, column=0)
# c5 = Checkbutton(root, text=" RSI(5)", variable=checkBoxRSIFive, onvalue=1, offvalue=0, font="Helvetica")
# c5.grid(row=8, column=0)
# c6 = Checkbutton(root, text=" MA(5)", variable=checkBoxMAFive, onvalue=1, offvalue=0, font="Helvetica")
# c6.grid(row=9, column=0)
#
# checkBoxEMATen = IntVar()
# checkBoxRSITen = IntVar()
# checkBoxMATen = IntVar()
#
# c7 = Checkbutton(root, text=" EMA(10)", variable=checkBoxEMATen, onvalue=1, offvalue=0, font="Helvetica")
# c7.grid(row=10, column=0)
# c8 = Checkbutton(root, text=" RSI(10)", variable=checkBoxRSITen, onvalue=1, offvalue=0, font="Helvetica")
# c8.grid(row=11, column=0)
# c9 = Checkbutton(root, text=" MA(10)", variable=checkBoxMATen, onvalue=1, offvalue=0, font="Helvetica")
# c9.grid(row=12, column=0)
#
# checkBoxEMAFifteen = IntVar()
# checkBoxRSIFifteen = IntVar()
# checkBoxMAFifteen = IntVar()
#
# c10 = Checkbutton(root, text=" EMA(15)", variable=checkBoxEMAFifteen, onvalue=1, offvalue=0, font="Helvetica")
# c10.grid(row=13, column=0)
# c11 = Checkbutton(root, text=" RSI(15)", variable=checkBoxRSIFifteen, onvalue=1, offvalue=0, font="Helvetica")
# c11.grid(row=14, column=0)
# c12 = Checkbutton(root, text=" MA(15)", variable=checkBoxMAFifteen, onvalue=1, offvalue=0, font="Helvetica")
# c12.grid(row=15, column=0)
#
#
# checkBoxEMAThirty = IntVar()
# checkBoxRSIThirty = IntVar()
# checkBoxMAThirty = IntVar()
#
# c13 = Checkbutton(root, text=" EMA(30)", variable=checkBoxEMAThirty, onvalue=1, offvalue=0, font="Helvetica")
# c13.grid(row=16, column=0)
# c14 = Checkbutton(root, text=" RSI(30)", variable=checkBoxRSIThirty, onvalue=1, offvalue=0, font="Helvetica")
# c14.grid(row=17, column=0)
# c15 = Checkbutton(root, text=" MA(30)", variable=checkBoxMAThirty, onvalue=1, offvalue=0, font="Helvetica")
# c15.grid(row=18, column=0)
#
#
# checkBoxEMASixty = IntVar()
# checkBoxRSISixty = IntVar()
# checkBoxMASixty = IntVar()
#
# c16 = Checkbutton(root, text=" EMA(60)", variable=checkBoxEMASixty, onvalue=1, offvalue=0, font="Helvetica")
# c16.grid(row=19, column=0)
# c17 = Checkbutton(root, text=" RSI(60)", variable=checkBoxRSISixty, onvalue=1, offvalue=0, font="Helvetica")
# c17.grid(row=20, column=0)
# c18 = Checkbutton(root, text=" MA(60)", variable=checkBoxMASixty, onvalue=1, offvalue=0, font="Helvetica")
# c18.grid(row=21, column=0)

if __name__ == "__main__":
    updatePriceLabelTwoMin()
    root.mainloop()
