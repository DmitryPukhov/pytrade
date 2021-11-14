# import talib as ta
from datetime import *
import logging
import pandas as pd

from model.feed.Asset import Asset
from model.feed.Level2 import Level2
from model.feed.Ohlcv import Ohlcv
from model.feed.Quote import Quote

pd.options.display.width = 0


class Strategy1:

    def __init__(self, feed, broker, config):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._broker = broker
        self.asset = Asset(config['sec_class'], config['sec_code'])
        self._last_processed_time = datetime.min
        self._process_interval = timedelta(seconds=10)
        self._feed.subscribe_feed(self.asset, self)

    def run(self):
        self._logger.info("Running")
        # Subscribe to receive feed for the asset

    def on_candle(self, ohlcv: Ohlcv):
        """
        Receive a new candle event from feed. self.feed.candles dataframe contains all candles including this one.
        """
        # Skip if too early for a new processing cycle
        self._logger.debug(f"Got new candle ohlcv={ohlcv}")
        if (datetime.now() - self._last_processed_time) < self._process_interval:
            return
        self._logger.debug(
            f"Processing new data. Previous: {self._last_processed_time}, now: {datetime.now()}, interval {self._process_interval} elapsed")
        self._logger.debug(
            f"Accumulated candles: {len(self._feed.candles)}, quotes:{len(self._feed.quotes)}, level2: {len(self._feed.level2)}")
        self._last_processed_time = datetime.now()

    def on_heartbeat(self):
        self._logger.debug(f"Got heartbeat")
        return

    def on_quote(self, quote: Quote):
        """
        Got a new quote. self.feed.quotes contains all quotes including this one
        """
        self._logger.debug(f"Got new quote: {quote}")

    def on_level2(self, level2: Level2):
        """
        Got new level2 data. self.feed.level2 contains all level2 records including this one
        """
        self._logger.debug(f"Got new level2: {level2}")
        return
