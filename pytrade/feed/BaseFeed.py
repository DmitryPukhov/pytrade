import logging
import pandas as pd
import datetime as dt
pd.options.display.width = 0


class BaseFeed:
    """
    Base class for any feed
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)

    def __init__(self, feed, sec_class, sec_code):
        self._feed = feed
        self.sec_class = sec_class
        self.sec_code = sec_code

        # Connecting to feed
        self._feed.level2_callbacks.add(self.on_level2)
        self._feed.candle_callbacks.add(self.on_candle)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False
        self._flag = False
        self._last_tick_time = self._last_heartbeat = dt.datetime.min

        # Main data with price etc.
        self.candles: pd.DataFrame = pd.DataFrame(
            columns=['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        self.candles.set_index(['datetime', 'ticker'], inplace=True)
        self.level2: pd.DataFrame = pd.DataFrame(columns=['datetime', 'ticker', 'price', 'bid_vol', 'ask_vol'])
        self.level2.set_index(['datetime', 'ticker', 'price'], inplace=True)

    @staticmethod
    def _ticker_of(asset_class, asset_code):
        return asset_class + '/' + asset_code

    def on_candle(self, asset_class, asset_code, dt, o, h, l, c, v):
        """
        New ohlc data received
        """
        # Add ohlc to data
        ticker = self._ticker_of(asset_class, asset_code)
        self.candles.at[(pd.to_datetime(dt), ticker), ['open', 'high', 'low', 'close', 'volume']] = [o, h, l, c, v]
        self._logger.debug("Received feed for time=%s, ticker: %s, data:%s", dt, ticker, [o, h, l, c, v])
        self._last_tick_time = dt

    def on_level2(self, asset_class, asset_code, dt, level2: dict):
        self._logger.debug("Received level2 for time = %s. %s/%s. Data: %s", dt, asset_class, asset_code, level2)
        ticker = self._ticker_of(asset_class, asset_code)
        for price in level2.keys():
            bid_vol = level2[price][0]
            ask_vol = level2[price][1]
            self.level2.at[(pd.to_datetime(dt), ticker, price), ['bid_vol', 'ask_vol']] = [bid_vol, ask_vol]
            self._last_tick_time = dt

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        self._last_heartbeat = dt.datetime.now()
