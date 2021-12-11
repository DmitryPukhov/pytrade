# import talib as ta
from datetime import *
import logging
import pandas as pd

from broker.Broker import Broker
from feed.Feed import Feed
from model.feed.Asset import Asset
from model.feed.Level2 import Level2
from model.feed.Ohlcv import Ohlcv
from model.feed.Quote import Quote
from strategy.features.Level2Features import Level2Features
from strategy.features.PriceFeatures import PriceFeatures
from strategy.features.TargetFeatures import TargetFeatures

pd.options.display.width = 0


class PeriodicalLearnStrategy:
    """
    Strategy based on periodical additional learning
    """

    def __init__(self, feed: Feed, broker: Broker, config):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._broker = broker
        self.asset = Asset(config['sec_class'], config['sec_code'])
        #self._last_big_learn_time = datetime.min
        self._last_big_learn_time = None
        # todo:: parameterise
        self._interval_big_learn = timedelta(seconds=10)
        self._interval_small_learn = timedelta(hours=2)
        self._feed.subscribe_feed(self.asset, self)
        self._logger.info(f"Strategy initialized with initial learn interval {self._interval_big_learn},"
                          f" additional learn interval ${self._interval_small_learn}")

    def big_learn(self):
        """
        Learn on all the data received
        """
        self._logger.info("Starting big learn")

        # Feature engineering
        level2_features = Level2Features().level2_buckets(self._feed.level2)
        target_features = TargetFeatures().min_max_future(self._feed.quotes, 5, 'min')
        price_features = PriceFeatures().prices(self._feed.quotes)

        # Set last learning time to the last quote time
        self._last_big_learn_time = self._feed.quotes.index[-1][0]
        self._logger.info(f"Completed big learn, last time: {self._last_big_learn_time}")

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
        if not self._last_big_learn_time:
            self._last_big_learn_time = quote.dt
        if (quote.dt - self._last_big_learn_time) >= self._interval_big_learn:
            self.big_learn()

    def on_level2(self, level2: Level2):
        """
        Got new level2 data. self.feed.level2 contains all level2 records including this one
        """
        self._logger.debug(f"Got new level2: {level2}")
        return
