# import talib as ta
from datetime import *
import logging
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

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

    def learn_on(self, quotes: pd.DataFrame, level2: pd.DataFrame):
        """Learning on price and level2 data"""
        # Get X,y for train/test
        X,y = FeatureEngineering().features_of(quotes, level2, 5, 'min', 3)
        n_splits = 5
        tscv = TimeSeriesSplit(n_splits)
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
