import logging
import pandas as pd
import datetime as dt

pd.options.display.width = 0


class BaseFeed:
    """
    Base class for any feed. Keeps quotes and level2 in pandas dataframes.
    """
    def __init__(self, feed, sec_class, sec_code):
        self._logger = logging.getLogger(__name__)

        # Connecting to feed
        self._feed = feed
        self.sec_class = sec_class
        self.sec_code = sec_code
        self._feed.subscribe_feed(self.sec_class, self.sec_code, self)

        self.last_tick_time = self.last_heartbeat = dt.datetime.min

        # Main data with price etc.
        self.candles: pd.DataFrame = pd.DataFrame(
            columns=['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        self.candles.set_index(['datetime', 'ticker'], inplace=True)
        self.level2: pd.DataFrame = pd.DataFrame(columns=['datetime', 'ticker', 'price', 'bid_vol', 'ask_vol'])
        self.level2.set_index(['datetime', 'ticker', 'price'], inplace=True)

    @staticmethod
    def _ticker_of(asset_class, asset_code):
        return asset_class + '/' + asset_code

    def on_quote(self, asset_class, asset_code, datetime, bid, ask, last):
        """
        New bid/ask received
        """
        self.last_tick_time = dt.datetime.now()
        ticker = self._ticker_of(asset_class, asset_code)
        self._logger.debug("Received quote, time=%s, ticker: %s, bid:%s, ask:%s, last:%s",
                           datetime, ticker, bid, ask, last)

    def on_candle(self, asset_class, asset_code, datetime, o, h, l, c, v):
        """
        New ohlc data received
        """
        # Add ohlc to data
        ticker = self._ticker_of(asset_class, asset_code)
        self.candles.at[(pd.to_datetime(datetime), ticker),
                        ['open', 'high', 'low', 'close', 'volume']] = [o, h, l, c, v]
        self._logger.debug("Received candle, time=%s, ticker: %s, data:%s", datetime, ticker, [o, h, l, c, v])
        self.last_tick_time = dt.datetime.now()

    def on_level2(self, asset_class, asset_code, datetime, level2: dict):
        """
        New level2 data received
        """
        self._logger.debug("Received level2 for time = %s. %s/%s. Data: %s", datetime, asset_class, asset_code, level2)
        ticker = self._ticker_of(asset_class, asset_code)
        for price in level2.keys():
            bid_vol = level2[price][0]
            ask_vol = level2[price][1]
            self.level2.at[(pd.to_datetime(datetime), ticker, price), ['bid_vol', 'ask_vol']] = [bid_vol, ask_vol]
            self.last_tick_time = dt.datetime.now()

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        self.last_heartbeat = dt.datetime.now()
