import itertools
import logging
from collections import defaultdict
import pandas as pd
from datetime import *
pd.options.display.width = 0


class Feed:
    """
    Base class for any feed. Keeps quotes and level2 in pandas dataframes.
    """

    def __init__(self, feed_adapter, sec_class, sec_code):
        self._logger = logging.getLogger(__name__)

        # Connecting to feed
        self._feed_adapter = feed_adapter
        self.sec_class = sec_class
        self.sec_code = sec_code

        self._subscribers = defaultdict(list)
        # self._feed.subscribe_feed(self.sec_class, self.sec_code, self)

        self.last_tick_time = self.last_heartbeat = datetime.min

        # Main data with price etc.
        self.candles: pd.DataFrame = pd.DataFrame(
            columns=['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume'])
        self.quotes: pd.DataFrame = pd.DataFrame(
            columns=['datetime', 'ticker', 'bid', 'ask', 'last']
        )
        self.candles.set_index(['datetime', 'ticker'], inplace=True)
        self.quotes.set_index(['datetime', 'ticker'], inplace=True)
        self.level2: pd.DataFrame = pd.DataFrame(columns=['datetime', 'ticker', 'price', 'bid_vol', 'ask_vol'])
        self.level2.set_index(['datetime', 'ticker', 'price'], inplace=True)

    def subscribe_feed(self, class_code, sec_code, subscriber):
        """
        Add subsciber for feed data
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param subscriber subscriber class, inherited from base feed
        """
        # Register given feed callback
        key = (class_code, sec_code)

        # Register given feed callback
        self._subscribers[key].append(subscriber)
        self._feed_adapter.subscribe_feed(self.sec_class, self.sec_code, self)

    @staticmethod
    def _ticker_of(asset_class, asset_code):
        return asset_class + '/' + asset_code

    def on_quote(self, asset_class, asset_code, dt, bid, ask, last):
        """
        New bid/ask received
        """
        self.last_tick_time = datetime.now()
        ticker = self._ticker_of(asset_class, asset_code)
        self._logger.debug("Received quote, time=%s, ticker: %s, bid:%s, ask:%s, last:%s",
                           dt, ticker, bid, ask, last)
        # Set to quotes pandas dataframe
        self.quotes.at[(pd.to_datetime(dt), ticker), ['bid', 'ask', 'last']] = [bid, ask, last]
        # Push the quote up to subscribers
        for subscriber in self._subscribers[(asset_class, asset_code)] + self._subscribers[("*", "*")]:
            if subscriber.on_quote:
                subscriber.on_quote(asset_class, asset_code, dt, bid, ask, last)

    def on_candle(self, asset_class, asset_code, dt, o, h, l_, c, v):
        """
        New ohlc data received
        """
        # Add ohlc to data
        ticker = self._ticker_of(asset_class, asset_code)
        self.candles.at[(pd.to_datetime(dt), ticker),
                        ['open', 'high', 'low', 'close', 'volume']] = [o, h, l_, c, v]
        self._logger.debug("Received candle, time=%s, ticker: %s, data:%s", dt, ticker, [o, h, l_, c, v])

        #  data to subscribers
        subscribers = self._subscribers[(asset_class, asset_code)] + self._subscribers[("*", "*")]
        push_list = set(filter(lambda s: callable(getattr(s, 'on_candle', None)), subscribers))
        for subscriber in push_list:
            subscriber.on_candle(asset_class, asset_code, dt, o, h, l_, c, v)
        self.last_tick_time = dt.datetime.now()

    def on_level2(self, asset_class, asset_code, dt, level2: dict):
        """
        New level2 data received
        """
        self._logger.debug("Received level2 for time = %s. %s/%s. Data: %s", datetime, asset_class, asset_code, level2)
        ticker = self._ticker_of(asset_class, asset_code)
        # Record new level2 to level2 pandas dataframe
        for price in level2.keys():
            bid_vol = level2[price][0]
            ask_vol = level2[price][1]
            self.level2.at[(pd.to_datetime(dt), ticker, price), ['bid_vol', 'ask_vol']] = [bid_vol, ask_vol]
            self.last_tick_time = datetime.now()

        # Push level2 event up
        subscribers = self._subscribers[(asset_class, asset_code)] + self._subscribers[("*", "*")]
        push_list = set(filter(lambda s: callable(getattr(s, 'on_level2', None)), subscribers))
        for subscriber in push_list:
            subscriber.on_level2(asset_class, asset_code, datetime, level2)

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        self._logger.debug("Got heartbeat event")
        subscribers = set(itertools.chain.from_iterable(self._subscribers.values()))
        push_list = set(filter(lambda s: callable(getattr(s,"on_heartbeat", None)), subscribers))
        for subscriber in push_list:
            subscriber.on_heartbeat()

        self.last_heartbeat = datetime.now()
    
    def _subscribers_of(self, asset, event):
        filter(lambda s: hasattr(s,event), set(self._subscribers[asset] + self._subscribers[("*", "*")]))
