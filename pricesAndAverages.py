import time
import robin_stocks.robinhood as r
import pandas as pd
import os.path as path
import talib
import numpy
from requests import HTTPError

import configurationFile

global data
data = pd.DataFrame
CRYPTO_CHOICE = configurationFile.config['COIN_CHOICE']

TWO_MIN = configurationFile.config['TWO_MIN']
FIVE_MIN = configurationFile.config['FIVE_MIN']
TEN_MIN = configurationFile.config['TEN_MIN']
FIFTEEN_MIN = configurationFile.config['FIFTEEN_MIN']
THIRTY_MIN = configurationFile.config['THIRTY_MIN']
ONE_HOUR = configurationFile.config['ONE_HOUR']
TWO_HOUR = configurationFile.config['TWO_HOUR']


# Returns the data of all of the prices and averages.
def getData():
    global data
    return data


# Gets the prices from RobinHood of the crypto you are wanting to trade.
def getPrices(coin=""):
    connection_timeout = 30
    start_time = time.time()
    while True:
        try:
            result = r.get_crypto_quote(coin)
            # price = result['mark_price']
            # print(str(round(float(result['bid_price']), 2)) + str(round(float(result['ask_price']), 2)))
            break
        except HTTPError as e:
            if e.code == 502:
                if time.time() > start_time + connection_timeout:
                    raise Exception('Unable to get updates after {} seconds of ConnectionErrors'.
                                    format(connection_timeout))
            else:
                time.sleep(1)  # attempting once every second
        # Ok, I've got 'em. Let's iterate through each one
        print("An exception occurred retrieving prices.")

    return result


# Loads the saved pickled dataframe into the pandas dataframe for use while the program is running.
# It creates a new file if this is the first time the program is being run.
def loadDataframe():
    global data
    if path.exists("dataframe.pickle"):
        data = pd.read_pickle('dataframe.pickle')
    else:
        column_names = ['exec_time', CRYPTO_CHOICE]
        data = pd.DataFrame(columns=column_names)

    return data


# This will save the pandas dataframe to a pickle file.
def saveState():
    global data
    data = data.iloc[1:]
    data.to_pickle('dataframe.pickle')


# This will update the pandas dataframe with the current prices and calculate the averages from the prices
# that are currently in the dataframe.
def updateDataframe(now, currentPrices=0.0):
    # we check this each time, so we don't need to lock for more than two cycles.
    # It will set back to two if it fails on the next pass.
    global data

    rowData = {}

    if currentPrices == 0:
        print("Exception received getting prices, not adding data, locking .s")
        return data

    rowData.update({'exec_time': now})

    rowData.update({CRYPTO_CHOICE: currentPrices})

    data = data.append(rowData, ignore_index=True)
    colName = "MA-2"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=TWO_MIN).mean(), 2)
    colName = "MA-5"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=FIVE_MIN).mean(), 2)
    colName = "MA-10"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=TEN_MIN).mean(), 2)
    colName = "MA-15"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=FIFTEEN_MIN).mean(), 2)
    colName = "MA-30"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=THIRTY_MIN).mean(), 2)
    colName = "MA-60"
    data[colName] = round(data[CRYPTO_CHOICE].shift(1).rolling(window=ONE_HOUR).mean(), 2)
    colName = "RSI-2"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=TWO_MIN))
    colName = "RSI-5"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=FIVE_MIN))
    colName = "RSI-10"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=TEN_MIN))
    colName = "RSI-15"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=FIFTEEN_MIN))
    colName = "RSI-30"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=THIRTY_MIN))
    colName = "RSI-60"
    data[colName] = (talib.RSI(data[CRYPTO_CHOICE].values, timeperiod=ONE_HOUR))
    colName = "EMA-2"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=TWO_MIN)
    colName = "EMA-5"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=FIVE_MIN)
    colName = "EMA-10"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=TEN_MIN)
    colName = "EMA-15"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=FIFTEEN_MIN)
    colName = "EMA-30"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=THIRTY_MIN)
    colName = "EMA-60"
    data[colName] = talib.EMA(data[CRYPTO_CHOICE].values, timeperiod=ONE_HOUR)
    colName = "-20% Below"
    data[colName] = round(numpy.percentile(data[CRYPTO_CHOICE].tail(TWO_HOUR), 20), 3)
    colName = "-20% Above"
    data[colName] = round(numpy.percentile(data[CRYPTO_CHOICE].tail(TWO_HOUR), 80), 3)

    saveState()
    return data
