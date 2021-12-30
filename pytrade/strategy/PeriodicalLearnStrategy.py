# import talib as ta
import glob
import os.path
from datetime import *
import logging

import keras.models
import pandas as pd
import sklearn
from sklearn import preprocessing, svm
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import MinMaxScaler
from statsmodels.tsa.arima.model import ARIMA
from broker.Broker import Broker
from connector.CsvFeedConnector import CsvFeedConnector
from feed.Feed import Feed
from model.feed.Asset import Asset
from model.feed.Level2 import Level2
from model.feed.Ohlcv import Ohlcv
from model.feed.Quote import Quote
from strategy.features.FeatureEngineering import FeatureEngineering
from strategy.features.Level2Features import Level2Features
from strategy.features.PriceFeatures import PriceFeatures
from strategy.features.TargetFeatures import TargetFeatures
from sklearn.model_selection import *
import numpy as np
# example of training a final classification model
from keras.models import Sequential
from keras.layers import Dense
import tensorflow as tf

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
        self.weights_path = 'weights/model1'
        self.model = self.model()
        self.pipeline = self.pipeline()

    def model(self):
        # loss='mean_squared_logarithmic_error'
        loss = 'huber'
        # Add layers
        model = Sequential()
        model.add(Dense(128, input_dim=32, activation='relu'))
        model.add(Dense(512, activation='relu'))
        model.add(Dense(1024, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(2, activation='relu'))
        model.compile(loss=loss, optimizer='adam')

        # Load weights

        if os.path.exists(self.weights_path+'.index'):
            self._logger.info(f"Load model weights in {self.weights_path}")
            model.load_weights(self.weights_path)
        else:
            self._logger.info(f"Model weights not found in {self.weights_path}")
        return model

    def pipeline(self):
        # Create pipeline
        return make_pipeline(preprocessing.MinMaxScaler(), self.model)

    def learn(self):
        """Learn on csv data"""
        # Read csv data
        _, quotes, level2 = self._csv_connector.read_csvs()
        quotes.set_index(["ticker"], append=True, inplace=True)
        level2.set_index(["ticker"], append=True, inplace=True)

        # Create the model
        X, y = FeatureEngineering().features_of(quotes, level2, 5, 'min', 3)

        # Learn
        self.learn_all(X, y)

        # Save weights
        self._logger.info(f"Save model weights to {self.weights_path}")
        self.model.save_weights(self.weights_path)

    def learn_day_by_day(self, X: pd.DataFrame, y: pd.DataFrame):
        """ Learn on prepared data, each learn cycle is inside one day"""
        # Cross validation
        n_splits = 15
        tscv = TimeSeriesSplit(n_splits)
        dates = np.unique(X.index.date)
        self._logger.info(f"Learning on dates {dates}")
        for date in dates:
            X_date = X[X.index.date == date]
            y_date = y[y.index.date == date]
            if X_date.empty or y_date.empty:
                self._logger.info(f"Data for {date} is empty")
                continue
            self._logger.info(f"Learning on {date} data")
            scores = cross_val_score(estimator=self.pipeline, X=X_date, y=y_date, cv=tscv, verbose=1, scoring='r2',
                                     n_jobs=4)
            print(scores)

    def learn_all(self, X: pd.DataFrame, y: pd.DataFrame):
        """Learning on all price and level2 data"""
        self._logger.info("Learn on whole data")
        # Cross validation
        n_splits = 100
        tscv = TimeSeriesSplit(n_splits)
        print(sorted(sklearn.metrics.SCORERS.keys()))
        # scores = cross_val_score(estimator=self.pipeline, X=X, y=y, cv=tscv, verbose=1, scoring='r2', n_jobs=4)
        # print(sorted(sklearn.metrics.SCORERS.keys()))
        scores = cross_val_score(estimator=self.pipeline, X=X, y=y, cv=tscv, verbose=1, scoring='explained_variance',
                                 n_jobs=4)
        print(scores)
        self._logger.info("split")

    def periodical_learn(self):
        """
        Learn on last data we have
        """
        self._logger.info("Starting periodical learn")
        X, y = FeatureEngineering().features_of(self._feed.quotes, self._feed.level2, 5, 'min', 3)
        self.learn_all(X, y)

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
