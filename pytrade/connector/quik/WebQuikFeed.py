import itertools
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Optional
from connector.quik.MsgId import MsgId
from connector.quik.WebQuikConnector import WebQuikConnector
from model.feed.Asset import Asset
from model.feed.Level2 import Level2
from model.feed.Level2Item import Level2Item
from model.feed.Ohlcv import Ohlcv
from model.feed.Quote import Quote

from websocket import ABNF


class WebQuikFeed:
    """
    Feed facade. Provides feed info from web quik connector to consumer.
    Parse feed messages from web quik.
    """

    #    def __init__(self, connector: WebQuikConnector):
    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self._connector = WebQuikConnector(config)
        self._connector.feed = self

        # Subscribers for data feed. {(class_code, sec_code): callback_func}
        self._feed_subscribers = defaultdict(list)
        self.callbacks = {MsgId.TRADE_SESSION_OPEN: self.on_trade_session_open,
                          MsgId.QUOTES: self._on_quotes,
                          MsgId.GRAPH: self._on_candle,
                          MsgId.LEVEL2: self._on_level2,
                          MsgId.HEARTBEAT: self.on_heartbeat
                          }
        self._connector.subscribe(self.callbacks)

    def run(self):
        self._connector.run_once()

    @staticmethod
    def _ticker_of(asset: Asset) -> Optional[str]:
        if not asset:
            return None
        return '|'.join([str(asset.class_code), str(asset.sec_code)])

    @staticmethod
    def _asset_of(quik_str: str) -> Optional[Asset]:
        # Example: "QJSIM¦SBER¦0", we need to streap trailing \0
        if not quik_str:
            return None
        # groups = re.search('([\\w\\d]+(?=\\|))*\\|*([\\w\\d]+)?', quik_str)
        # groups = re.match('(?P<class_code>[\\w\\d]+(?=\\|))?\\|?(?P<sec_code>[\\w\\d]+)', quik_str)
        groups = re.match('(?P<class_code>[\\w\\d]+(?=¦))?¦?(?P<sec_code>[\\w\\d]+)', quik_str)
        asset = Asset(groups["class_code"], groups["sec_code"])
        return asset

    @staticmethod
    def _ohlcv_of(asset_str: str, quik_ohlcv: dict) -> Ohlcv:
        return Ohlcv(
            datetime.fromisoformat(quik_ohlcv['d']),
            WebQuikFeed._asset_of(asset_str),
            quik_ohlcv['o'],
            quik_ohlcv['h'],
            quik_ohlcv['l'],
            quik_ohlcv['c'],
            quik_ohlcv['v'])

    @staticmethod
    def _quote_of(ticker: str, quik_quote: dict) -> Quote:
        return Quote(
            dt=datetime.now(),
            asset=WebQuikFeed._asset_of(ticker),
            bid=quik_quote.get('bid'),
            ask=quik_quote.get('offer'),
            last=quik_quote.get('last'),
            last_change=quik_quote.get('lastchange'))

    @staticmethod
    def _level2_of(dt, asset: str, quik_level2: dict):
        # {'22806': {'b': 234, 's': 0, 'by': 0, 'sy': 0}
        level2 = Level2(dt, asset)
        for key in quik_level2.keys():
            # Parse price, bid volume, ask volume
            price = float(key)
            bid_vol = quik_level2[key]['b']
            if bid_vol == 0:
                bid_vol = None
            ask_vol = quik_level2[key]['s']
            if ask_vol == 0:
                ask_vol = None
            # Add price, bid vol, ask vol to level 2 prices
            level2.items.add(Level2Item(price, bid_vol, ask_vol))

        return level2

    def on_message(self, msg):
        callback = self.callbacks.get(msg['msgid'])
        if callback:
            callback(msg)

    def _request_feed(self, asset: Asset):
        """
        Request candles and level2 data from quik
        """
        # Request quotes
        self._logger.info(f"Requesting quotes for asset {asset}")
        msg = '{"msgid":%s,"c":"%s","s":"%s","p":%s}' % (
            MsgId.CREATE_DATASOURCE, asset.class_code, asset.sec_code, 0)
        msg = msg.encode()
        self._logger.debug('Sending msg: %s' % msg)
        self._connector.websocket_app.send(msg)
        # Request level2 data
        self._logger.info(f"Requesting level2 data for asset {asset}")
        depth = 30
        msg = '{"msgid":%s,"c":"%s","s":"%s","depth":%s}' % \
              (MsgId.CREATE_LEVEL2_DATASOURCE, asset.class_code, asset.sec_code, depth)
        self._logger.debug('Sending msg: %s' % msg)
        self._connector.websocket_app.send(msg, opcode=ABNF.OPCODE_BINARY)

    def subscribe_feed(self, asset: Asset, subscriber):
        """
        Add subsciber for feed data
        """

        # Register given feed callback
        self._feed_subscribers[asset].append(subscriber)

        # Request this feed from server
        if self._connector.status == WebQuikConnector.Status.CONNECTED:
            self._request_feed(asset)

    def on_trade_session_open(self, msg):
        """
        On start, trade session is opened. Now we can request data and set orders
        """
        self._logger.debug(f"Trade session opened. Requesting feeds for subscribers: {self._feed_subscribers}")
        for asset in filter(lambda a: a != Asset.any_asset(), self._feed_subscribers):
            self._request_feed(asset)

    def _on_quotes(self, data: dict):
        """
        Bid/ask spreads callback
        Msg sample: {"msgid":21011,"dataResult":{"CETS\u00A6BYNRUBTODTOM":{"bid":0, "ask":10, last":0,"lastchange":...
        """
        self._logger.debug('Got bid/ask quotes: %s', data)
        for quik_asset in data['dataResult'].keys():
            asset = WebQuikFeed._asset_of(quik_asset)
            if asset in self._feed_subscribers.keys():
                quote = WebQuikFeed._quote_of(quik_asset, data['dataResult'][quik_asset])
                # Send to subscriber
                for subscriber in self._feed_subscribers[asset] + self._feed_subscribers[Asset.any_asset()]:
                    subscriber.on_quote(quote)

    def _on_candle(self, data: dict):
        """
        Ohlc data callback
        :param data: dict like {"msgid":21016,"graph":{"QJSIM\u00A6SBER\u00A60":[{"d":"2019-10-01
        10:02:00","o":22649,"c":22647,"h":22649,"l":22646,"v":1889}]}} :return:
        """
        self._logger.debug('Got candles: %s', data)

        # Todo: get rid of nested check
        for asset_str in data['graph'].keys():
            # Each asset in data['graph']
            asset = WebQuikFeed._asset_of(asset_str)

            if asset not in self._feed_subscribers:
                continue
            asset_data = data['graph'][asset_str]
            for quik_ohlcv in asset_data:
                # Each ohlcv for this asset
                ohlcv = WebQuikFeed._ohlcv_of(asset_str,quik_ohlcv)

                # Send the candle to rabbitmq
                # self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.CANDLES, body=str(ohlcv))

                # Send data to subscribers
                subscribers = self._feed_subscribers[asset] + self._feed_subscribers[self.any_asset]
                for subscriber in set(filter(lambda s: s.on_candle, subscribers)):
                    subscriber.on_candle(ohlcv)

    def _on_level2(self, data: dict):
        """
        Level 2 data handler. Quik sends us full level2 snapshot.
        """
        # Sample of level2. {'msgid': 21014, 'quotes': {'QJSIM¦SBER': {'lines': {'22806':
        # {'b': 234, 's': 0, 'by': 0, 'sy': 0}, '22841': {'b': 437, 's': 0, 'by': 0, 'sy': 0},
        # '22853': {'b': 60, 's': 0, 'by': 0, 'sy': 0}, '22878': {'b': 82, 's': 0, 'by': 0, 'sy': 0},
        # '22886': {'b': 138, 's': 0, 'by': 0, 'sy': 0}, '22895': {'b': 1, 's': 0, 'by': 0, 'sy': 0},...

        # Go through all assets in level2 message
        # Todo: get rid of nested check
        for asset_str in data['quotes']:
            # asset_class, asset_code = self._connector.asset2tuple(asset_str)
            asset = WebQuikFeed._asset_of(asset_str)
            if asset not in self._feed_subscribers:
                continue
            # {'22806':  {'b': 234, 's': 0, 'by': 0, 'sy': 0}, ..}
            level2_quik: dict = data['quotes'][asset_str]['lines']
            # level2 = {}
            # Level2(datetime.now())
            # Fill in level2 items
            items = []
            for key in level2_quik.keys():
                price = int(key)
                bid = level2_quik[key]['b']
                if bid == 0:
                    bid = None
                ask = level2_quik[key]['s']
                if ask == 0:
                    ask = None
                items.append(Level2Item(price, bid, ask))

            level2 = Level2.of(datetime.now(),asset, items)

            # If somebody subscribed to level2 of this asset, send her this data.
            subscribers = self._feed_subscribers[asset] + self._feed_subscribers[Asset.any_asset()]
            for subscriber in filter(lambda s: s.on_level2, subscribers):
                subscriber.on_level2(level2)

    def on_heartbeat(self, *args):
        """
        Pass heartbeat event to feed consumer
        """
        # Get only subscribers who has on_heartbeat callback
        for subscriber in filter(lambda s: s.on_heartbeat,
                                 itertools.chain.from_iterable(self._feed_subscribers.values())):
            subscriber.on_heartbeat()
