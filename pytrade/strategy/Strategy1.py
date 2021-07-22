# import talib as ta
from datetime import *
import logging
import pandas as pd
pd.options.display.width = 0


class Strategy1:

    def __init__(self, feed, broker, config):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._broker = broker
        self._sec_class = config['sec_class']
        self._sec_code = config['sec_code']
        self._last_processed_time = datetime.min
        self._process_interval = timedelta(seconds=10)
        self._feed.subscribe_feed(self._sec_class, self._sec_code, self)

    def run(self):
        self._logger.info("Running")
        # Subscribe to receive feed for the asset

    def on_candle(self,asset_class, asset_code, dt, o, h, l_, c, v):
        """
        Receive a new candle event from feed. self.feed.candles dataframe contains all candles including this one.
        """
        # Skip if too early for a new processing cycle
        self._logger.debug(f"Got new candle, asset: {(asset_class, asset_code)}, dt={dt},o={o},h={h},l={l_},c={c}")
        if (datetime.now() - self._last_processed_time) < self._process_interval:
            return
        self._logger.debug(f"Processing new data. Previous: {self._last_processed_time}, now: {datetime.now()}, interval {self._process_interval} elapsed")
        self._logger.debug(f"Accumulated candles: {len(self._feed.candles)}, quotes:{len(self._feed.quotes)}, level2: {len(self._feed.level2)}")
        self._last_processed_time = datetime.now()

    # def on_heartbeat(self):
    #     self._logger.debug(f"Got heartbeat")
    #     return

    # def on_quote(self, asset_class, asset_code, dt, bid, ask, last):
    #     """
    #     Got a new quote. self.feed.quotes contains all quotes including this one
    #     """
    #     #self._logger.debug(f"Got new quote,  asset: {(asset_class, asset_code)}, dt={dt}, bid={bid}, ask={ask}, last={last}")
    #     return
    #
    # def on_level2(self, asset_class, asset_code, datetime, level2: dict):
    #     """
    #     Got new level2 data. self.feed.level2 contains all level2 records including this one
    #     """
    #     #self._logger.debug(f"Got new level2, asset: {(asset_class, asset_code)} dt: {datetime}, level2: {level2}")
    #     return

