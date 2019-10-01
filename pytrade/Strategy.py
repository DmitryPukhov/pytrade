import logging
#import talib as ta
import pandas as pd
import datetime as dt


class Strategy:
    """
    Strategy receives data from feed and make orders to broker
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, broker, sec_class, sec_code):
        self._feed = feed
        self.sec_class = sec_class
        self.sec_code = sec_code

        # Connecting to broker
        self._broker = broker

        # Connecting to feed
        self._feed.feed_callbacks.add(self.on_feed)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False
        self._flag = False
        self._last_tick_time = dt.datetime.min

        # Main data with price etc.
        self.data = pd.DataFrame(columns=['price', 'vol'])

    def on_feed(self, asset_class, asset, dt, o, h, l, c, v):

        """
        New price/vol tick received
        """
        # Add tick to data
        self.data.loc[pd.to_datetime(dt)] = [c, v]
        self._logger.debug("Received ohlc: time=%s, asset=%s\\%s, price=%s, vol=%s", dt, asset_class, asset, c, v)
        self._last_tick_time = dt

    def on_heartbeat(self):
        """
        Heartbeat received
        :return: None
        """
