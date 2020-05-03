from connector.quik.MsgId import MsgId
import websocket
from datetime import datetime
from websocket import WebSocketApp, ABNF
import json
import logging
from connector.quik.WebQuikConnector import WebQuikConnector


class WebQuikFeed:
    """
    Feed facade. Provides feed info from web quik connector to consumer.
    Parse feed messages from web quik.
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, connector: WebQuikConnector):
        self._connector = connector
        self._connector.feed = self

        # Subscribers for data feed. {(class_code, sec_code): callback_func}
        self._feed_subscribers = {}
        self._callbacks = {MsgId.MSG_ID_QUOTES: self._on_quotes,
                           MsgId.MSG_ID_GRAPH: self._on_candle,
                           MsgId.MSG_ID_LEVEL2: self._on_level2,
                           }

    def on_message(self, msg):
        callback = self._callbacks.get(msg['msgid'])
        if callback:
            callback(msg)

    def _request_feed(self, class_code, sec_code):
        """
        Request candles and level2 data from quik
        """
        # Request quotes
        self._logger.info('Requesting quotes for %s\\%s', class_code, sec_code)
        msg = '{"msgid":%s,"c":"%s","s":"%s","p":%s}' % (MsgId.MSG_ID_CREATE_DATASOURCE, class_code, sec_code, 0)
        msg = msg.encode()
        self._logger.debug('Sending msg: %s' % msg)
        self._connector.websocket_app.send(msg)
        # Request level2 data
        self._logger.info('Requesting level2 data for %s\\%s', class_code, sec_code)
        depth = 30
        msg = '{"msgid":%s,"c":"%s","s":"%s","depth":%s}' % \
              (MsgId.MSG_ID_CREATE_LEVEL2_DATASOURCE, class_code, sec_code, depth)
        self._logger.debug('Sending msg: %s' % msg)
        self._connector.websocket_app.send(msg, opcode=ABNF.OPCODE_BINARY)

    def subscribe_feed(self, class_code, sec_code, subscriber):
        """
        Add subsciber for feed data
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param subscriber subscriber class, inherited from base feed
        """
        key = (class_code, sec_code)

        # Register given feed callback
        self._feed_subscribers[key] = subscriber

        # Request this feed from server
        if self._connector.status == WebQuikConnector.Status.CONNECTED:
            self._request_feed(class_code, sec_code)

    def on_trade_session_open(self, msg):
        """
        On start, trade session is opened. Now we can request data and set orders
        """
        for (class_code, sec_code), value in self._feed_subscribers.items():
            self._request_feed(class_code, sec_code)

    def _on_quotes(self, data: dict):
        """
        Bid/ask spreads callback
        Msg sample: {"msgid":21011,"dataResult":{"CETS\u00A6BYNRUBTODTOM":{"bid":0, "ask":10, last":0,"lastchange":...
        """
        self._logger.debug('Got bid/ask: %s', data)
        for asset_str in data['dataResult'].keys():
            (asset_class, asset_code) = self._connector.asset2tuple(asset_str)
            if (asset_class, asset_code) in self._feed_subscribers.keys():
                bid = data['dataResult'][asset_str]['bid']
                ask = data['dataResult'][asset_str]['offer']
                last = data['dataResult'][asset_str].get('last')
                # Send to subscriber
                self._feed_subscribers[(asset_class, asset_code)] \
                    .on_quote(asset_class, asset_code, datetime.now(), bid, ask, last)

    def _on_candle(self, data: dict):
        """
        Ohlc data callback
        :param data: dict like {"msgid":21016,"graph":{"QJSIM\u00A6SBER\u00A60":[{"d":"2019-10-01
        10:02:00","o":22649,"c":22647,"h":22649,"l":22646,"v":1889}]}} :return:
        """
        self._logger.debug('Got feed: %s', data)

        # Todo: get rid of nested check
        for asset_str in data['graph'].keys():
            # Each asset in data['graph']
            (asset_class, asset_code) = self._connector.asset2tuple(asset_str)
            if self._feed_subscribers[(asset_class, asset_code)] is not None:
                asset_data = data['graph'][asset_str]
                for ohlcv in asset_data:
                    # Each ohlcv for this asset
                    dt = datetime.fromisoformat(ohlcv['d'])
                    o = ohlcv['o']
                    h = ohlcv['h']
                    l_ = ohlcv['l']
                    c = ohlcv['c']
                    v = ohlcv['v']
                    # Send data to subscribers
                    self._feed_subscribers[(asset_class, asset_code)] \
                        .on_candle(asset_class, asset_code, dt, o, h, l_, c, v)

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
            asset_class, asset_code = self._connector.asset2tuple(asset_str)
            if self._feed_subscribers[(asset_class, asset_code)] is not None:
                # {'22806':  {'b': 234, 's': 0, 'by': 0, 'sy': 0}, ..}
                level2_quik: dict = data['quotes'][asset_str]['lines']
                level2 = {}
                for key in level2_quik.keys():
                    price = int(key)
                    bid = level2_quik[key]['b']
                    if bid == 0:
                        bid = None
                    ask = level2_quik[key]['s']
                    if ask == 0:
                        ask = None
                    level2[price] = (bid, ask)

                    # If somebody subscribed to level2 of this asset, send her this data.
                self._feed_subscribers[(asset_class, asset_code)].on_level2(asset_class, asset_code, datetime.now(),
                                                                            level2)

    def on_heartbeat(self):
        """
        Pass heartbeat event to feed consumer
        """
        for subscriber in self._feed_subscribers.values():
            subscriber.on_heartbeat()
