# import talib as ta
from datetime import *
import logging

import keras.models
import pandas as pd
import sklearn
from sklearn import *
from sklearn.metrics import *
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
from pytrade.broker.Broker import Broker
from pytrade.connector.CsvFeedConnector import CsvFeedConnector
from pytrade.feed.Feed import Feed
from pytrade.model.feed.Asset import Asset
from pytrade.model.feed.Level2 import Level2
from pytrade.model.feed.Ohlcv import Ohlcv
from pytrade.model.feed.Quote import Quote
from pytrade.strategy.features.FeatureEngineering import FeatureEngineering
from pytrade.strategy.features.Level2Features import Level2Features
from pytrade.strategy.features.PriceFeatures import PriceFeatures
from pytrade.strategy.features.TargetFeatures import TargetFeatures
from sklearn.model_selection import *
# example of training a final classification model
from keras.models import Sequential
from keras.layers import Dense

pd.options.display.width = 0


class PeriodicalLearnStrategy:
    """
    Strategy based on periodical additional learning
    """

    def __init__(self, feed: Feed, broker: Broker, config):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._broker = broker
        self.asset = Asset(config['trade.asset.sec_class'], config['trade.asset.sec_code'])
        # self._last_big_learn_time = datetime.min
        self._last_learn_time = None
        # todo:: parameterise
        self._interval_big_learn = timedelta(seconds=10)
        self._interval_small_learn = timedelta(hours=2)
        self._csv_connector = CsvFeedConnector(config)
        self._feed.subscribe_feed(self.asset, self)
        self._logger.info(f"Strategy initialized with initial learn interval {self._interval_big_learn},"
                          f" additional learn interval ${self._interval_small_learn}")

    def learn(self):
        _, quotes, level2 = self._csv_connector.read_csvs()
        quotes.set_index(["ticker"], append=True, inplace=True)
        level2.set_index(["ticker"], append=True, inplace=True)
        self.learn_on(quotes, level2)

    def model(self):
        model = Sequential()
        model.add(Dense(128,  input_dim=32, activation='relu'))
        model.add(Dense(256, activation='relu'))
        model.add(Dense(2,  activation='relu'))
        #model.compile(loss='binary_crossentropy', optimizer='adam')
        model.compile(loss='mean_squared_error', optimizer='adam')
        return model

    def learn_on(self, quotes: pd.DataFrame, level2: pd.DataFrame):
        """Learning on price and level2 data"""
        # Get unscaled X,y for train/test
        X, y = FeatureEngineering().features_of(quotes, level2, 5, 'min', 3)
        # Pipeline: scaler + model
        model = self.model()
        #model.fit(X,y)
        pipeline = make_pipeline(preprocessing.MinMaxScaler(), model)

        # Cross validation
        n_splits = 5
        tscv = TimeSeriesSplit(n_splits)
        # scoring: r2, mse
        self._logger.info(f"Possible scorings:{sorted(sklearn.metrics.SCORERS.keys())}")
        scores = cross_val_score(estimator=pipeline,X=X, y=y, cv=tscv, verbose=1, scoring='r2',n_jobs=1, error_score='raise')
        scores
        #cv=cross_validate(estimator=pipeline,X=X, y=y, cv=tscv, verbose=1,scoring='r2')

        self._logger.info(f"cross_val_score:{scores}")
        # todo: build a model and learn

    def periodical_learn(self):
        """
        Learn on last data we have
        """
        self._logger.info("Starting periodical learn")
        self.learn_on(self._feed.quotes, self._feed.level2)

        # Set last learning time to the last quote time
        self._last_learn_time = self._feed.quotes.index[-1][0]
        self._logger.info(f"Completed periodical learn, last time: {self._last_learn_time}")

    def run(self):
        self._logger.info("Running")
        # Subscribe to receive feed for the asset

    def on_candle(self, ohlcv: Ohlcv):
        """
        Receive a new candle event from feed. self.feed.candles dataframe contains all candles including this one.
        """
        # Skip if too early for a new processing cycle
        self._logger.debug(f"Got new candle ohlcv={ohlcv}")

    def on_heartbeat(self):
        self._logger.debug(f"Got heartbeat")
        return

    def on_quote(self, quote: Quote):
        """
        Got a new quote. self.feed.quotes contains all quotes including this one
        """
        self._logger.debug(f"Got new quote: {quote}")
        if not self._last_learn_time:
            self._last_learn_time = quote.dt
        if (quote.dt - self._last_learn_time) >= self._interval_big_learn:
            self.periodical_learn()

    def on_level2(self, level2: Level2):
        """
        Got new level2 data. self.feed.level2 contains all level2 records including this one
        """
        self._logger.debug(f"Got new level2: {level2}")
        return
