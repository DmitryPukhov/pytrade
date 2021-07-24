import itertools
import logging
from collections import defaultdict
from datetime import *
import pandas as pd

from model.feed.Asset import Asset
from model.feed.Level2 import Level2
from model.feed.Ohlcv import Ohlcv
from model.feed.Quote import Quote

pd.options.display.width = 0


class Feed:
    """
    Base class for any feed. Keeps quotes and level2 in pandas dataframes.
    """

    def __init__(self, feed_adapter):
        self._logger = logging.getLogger(__name__)

        # Connecting to feed
        self._feed_adapter = feed_adapter

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
        #self.level2: pd.DataFrame = pd.DataFrame(columns=['datetime', 'ticker', 'price', 'items'])
        self.level2.set_index(['datetime', 'ticker', 'price'], inplace=True)

    def subscribe_feed(self, asset: Asset, subscriber):
        """
        Add subsciber for feed data
        """
        # Register given feed callback
        self._subscribers[asset].append(subscriber)
        self._feed_adapter.subscribe_feed(asset, self)

    @staticmethod
    def _ticker_of(asset_class, asset_code):
        return asset_class + '/' + asset_code

    def on_quote(self, asset: Asset, quote: Quote):
        """
        New bid/ask received
        """
        self.last_tick_time = datetime.now()
        self._logger.debug(f"Received quote, asset: {asset}, quote: {quote}")
        # Set to quotes pandas dataframe
        self.quotes.at[(quote.dt, str(asset)), ['bid', 'ask', 'last']] = [quote.bid, quote.ask, quote.last]
        # Push the quote up to subscribers
        subscribers = self._subscribers[asset] + self._subscribers[Asset("*", "*")]
        push_list = set(filter(lambda s: callable(getattr(s, 'on_quote', None)), subscribers))
        for subscriber in push_list:
            subscriber.on_quote(asset, quote)

    def on_candle(self, asset: Asset, ohlcv: Ohlcv):
        """
        New ohlc data received
        """
        # Add ohlc to data
        self.candles.at[(ohlcv.dt, str(asset)),
                        ['open', 'high', 'low', 'close', 'volume']] = [ohlcv.o, ohlcv.h, ohlcv.l, ohlcv.c, ohlcv.v]
        self._logger.debug(f"Received candle for asset {asset}, candle: {ohlcv}")

        #  Push data to subscribers
        subscribers = self._subscribers[asset] + self._subscribers[Asset("*", "*")]
        push_list = set(filter(lambda s: callable(getattr(s, 'on_candle', None)), subscribers))
        for subscriber in push_list:
            subscriber.on_candle(asset,ohlcv)
        self.last_tick_time = datetime.now()

    def on_level2(self, asset: Asset, level2: Level2):
        """
        New level2 data received
        """
        self._logger.debug(f"Received level2 for asset {asset}, level2 {level2}")
        # Add new level2 records to dataframe
        for item in level2.items:
            self.level2.at[(level2.dt, str(asset), item.price),['bid_vol', 'ask_vol']] = [item.bid_vol, item.ask_vol]
        # Push level2 event up
        subscribers = self._subscribers[asset] + self._subscribers[Asset("*", "*")]
        push_list = set(filter(lambda s: callable(getattr(s, 'on_level2', None)), subscribers))
        for subscriber in push_list:
            subscriber.on_level2(asset, level2)

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        self._logger.debug("Got heartbeat event")
        subscribers = set(itertools.chain.from_iterable(self._subscribers.values()))
        push_list = set(filter(lambda s: callable(getattr(s, "on_heartbeat", None)), subscribers))
        for subscriber in push_list:
            subscriber.on_heartbeat()

        self.last_heartbeat = datetime.now()
