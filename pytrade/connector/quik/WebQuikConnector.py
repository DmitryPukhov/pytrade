import json
import logging
from datetime import datetime
from enum import Enum
import websocket
from websocket import WebSocketApp, ABNF

from pytrade.feed.BaseFeed import BaseFeed


class WebQuikConnector:
    """
    Socket interactions with WebQuik server.
    Use web quik server, login and password, provided by broker.
    Demo account could be created chere: https://junior.webquik.ru
    ToDo: process quotes 21016 and level2 21014 messages instead of general data 21011
    """

    # Connector possible statuses:
    class Status(Enum):
        CONNECTING = 0
        CONNECTED = 1
        BUSY = 2
        DISCONNECTING = 3
        DISCONNECTED = 4

    # Responce codes starts from 2 {mapIdName:{20000:"Авторизация",20001:"Запрос PIN",20002:"Ответ на запрос длины
    # пароля",20003:"Ответ на запрос смены пароля",20004:"Сообщения авторизации",20005:"Результат сохранения
    # профиля",20008:"Статус соединения",20014:"Сообщения сервера",21000:"Классы",21001:"Заявки",21003:"Сделки",
    # 21004:"Денежн.лимиты",21005:"Бумаж.лимиты",21006:"Ограничения",21007:"Позиции",21008:"Сообщения брокера",
    # 21009:"Ответы на транзакции",21011:"Основные торги",t21011:"Торги для ТТП",21012:"Купить/Продать",
    # 21013:"Портфель",21014:"Стаканы",21015:"Ответ по RFS",21016:"Графики",21017:"Новости",21018:"Тексты новостей",
    # 21019:"Валютные пары",21020:"Инфо по бумаге",21021:"Котировки RFS",21022:"Торговые счета",21023:"Торги по
    # вал.парам",21024:"Список вал.пар",22000:"Ответ по заявке",22001:"Ответ по стоп-заявке",22002:"Ответ по
    # связ.стоп-заявке",22003:"Ответ по услов.стоп-заявке",22004:"Ответ по FX-заявке",22100:"Ответ по снятию заявки",
    # 22101:"Ответ по снятию стоп-заявки"},
    _MSG_ID_AUTH = 20006
    _MSG_ID_TRADE_SESSION_OPEN = 20000
    _MSG_ID_EXIT = 10006
    _MSG_ID_CREATE_DATASOURCE = 11016
    _MSG_ID_CREATE_LEVEL2_DATASOURCE = 11014
    _MSG_ID_DATA = 21011
    _MSG_ID_GRAPH = 21016
    _MSG_ID_LEVEL2 = 21014
    _HEARTBEAT_SECONDS = 3

    _logger = logging.getLogger(__name__)
    _logger.setLevel("INFO")

    def __init__(self, conn, account, passwd):
        # Create websocket, not open and run here
        self._conn = conn
        self._ws: WebSocketApp = websocket.WebSocketApp(self._conn,
                                                        on_message=self._on_message,
                                                        on_error=self._on_error,
                                                        on_close=self._on_close,
                                                        on_pong=self._on_heartbeat)
        self._ws.on_open = self._on_socket_open

        self._passwd = passwd
        self._account = account
        self._last_trans_id = 0
        self.status = self.Status.DISCONNECTED

        # Callbacks for different messages msgid
        # Socket callback self._on_message will call these
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth,
                           self._MSG_ID_TRADE_SESSION_OPEN: self._on_trade_session_open,
                           # self._MSG_ID_DATA: self._on_data,
                           self._MSG_ID_GRAPH: self._on_candle,
                           self._MSG_ID_LEVEL2: self._on_level2
                           }

        # Subscribers for data feed
        self._feed_subscribers = {}
        #        self._level2_subscribers = {}

        # Broker information subscribers
        #        self.broker_subscribers = []
        # Heart beat support
        #        self.heartbeat_subscribers = set()
        self._heartbeat_cnt = 0

    def start(self):
        """
        Create web socket and run loop
        """
        if self.status == WebQuikConnector.Status.DISCONNECTED:
            self.status = WebQuikConnector.Status.CONNECTING
            self._logger.info("Connecting to " + self._conn)
            # Run loopo
            self._ws.run_forever(ping_interval=self._HEARTBEAT_SECONDS)

    def _on_socket_open(self):
        """
        Socket on_open handler
        Login just after web socket has been opened
        """
        auth_msg = '{"msgid":10000,"login":"' + self._account + '","password":"' + self._passwd \
                   + '","width":"200","height":"200","userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
                     '(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36","lang":"ru",' \
                     '"sid":"144f9.2b851e74","version":"6.6.1"} '
        self._ws.send(auth_msg)

    def _on_trade_session_open(self, msg):
        """
        Trade session is opened. Now we can request data and set orders
        """
        if msg['resultCode'] == 0:
            self._logger.info('Authenticated')
            self.status = WebQuikConnector.Status.CONNECTED
            self._logger.info('Connected. Trade session is opened')
            # Request feeds for subscribers from server
            for (class_code, sec_code), value in self._feed_subscribers.items():
                self._request_feed(class_code, sec_code)
        else:
            # Not opened, failure failed
            self.status = WebQuikConnector.Status.DISCONNECTED
            self.close()
            raise ConnectionError('Trade session opening failure: %s' % msg)

    def _on_auth(self, msg):
        """
        Authentication has passed, subscribe the feed and broker.
        """
        if msg['resultCode'] == 0:
            self._logger.info('Authenticated')
        else:
            # Auth failed
            self.status = WebQuikConnector.Status.DISCONNECTED
            self.close()
            raise ConnectionError('Authentication failure: %s' % msg)

    def _request_feed(self, class_code, sec_code):
        """
        Request candles and level2 data from quik
        """
        # Request quotes
        self._logger.info('Requesting quotes for %s\\%s', class_code, sec_code)
        msg = '{"msgid":%s,"c":"%s","s":"%s","p":%s}' % (self._MSG_ID_CREATE_DATASOURCE, class_code, sec_code, 0)
        msg = msg.encode()
        self._logger.debug('Sending msg: %s' % msg)
        self._ws.send(msg)
        # Request level2 data
        self._logger.info('Requesting level2 data for %s\\%s', class_code, sec_code)
        depth = 30
        msg = '{"msgid":%s,"c":"%s","s":"%s","depth":%s}' % \
              (self._MSG_ID_CREATE_LEVEL2_DATASOURCE, class_code, sec_code, depth)
        self._logger.debug('Sending msg: %s' % msg)
        self._ws.send(msg, opcode=ABNF.OPCODE_BINARY)

    def _on_message(self, raw_msg):
        """
        Entry for message processing. Call specific processors for different messages.
        """
        strmsg = raw_msg.decode()
        self._logger.debug('Got msg %s', strmsg)
        msg = json.loads(strmsg)
        # Find and execute callback function for this message
        callback = self._callbacks.get(msg['msgid'])
        if callback:
            callback(msg)

    @staticmethod
    def _asset2tuple(s):
        """
        Converts quik asset string to tuple(class, code)
        """
        # Split s and return first 2 parts - class and code
        parts: list = s.split("¦")
        return tuple([parts[0], parts[1]])

    @staticmethod
    def _tuple2asset(t: tuple):
        """
        Converts asset tuple(class, code) to quik compatible string class¦code
        """
        return "%s¦%s" % (t[0], t[1])

    def _on_candle(self, data: dict):
        """
        Ohlc data callback
        :param data: dict like {"msgid":21016,"graph":{"QJSIM\u00A6SBER\u00A60":[{"d":"2019-10-01
        10:02:00","o":22649,"c":22647,"h":22649,"l":22646,"v":1889}]}} :return:
        """
        self._logger.debug('Got feed: %s', data)

        for asset_str in data['graph'].keys():
            # Each asset in data['graph']
            (asset_class, asset_code) = self._asset2tuple(asset_str)
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
                self._feed_subscribers[(asset_class, asset_code)].on_candle(asset_class, asset_code, dt, o, h, l_, c, v)

    def _on_level2(self, data: dict):
        """
        Level 2 data handler. Quik sends us full level2 snapshot.
        """
        # Sample of level2. {'msgid': 21014, 'quotes': {'QJSIM¦SBER': {'lines': {'22806':
        # {'b': 234, 's': 0, 'by': 0, 'sy': 0}, '22841': {'b': 437, 's': 0, 'by': 0, 'sy': 0},
        # '22853': {'b': 60, 's': 0, 'by': 0, 'sy': 0}, '22878': {'b': 82, 's': 0, 'by': 0, 'sy': 0},
        # '22886': {'b': 138, 's': 0, 'by': 0, 'sy': 0}, '22895': {'b': 1, 's': 0, 'by': 0, 'sy': 0},...

        # Go through all assets in level2 message
        for asset_str in data['quotes']:
            asset_class, asset_code = self._asset2tuple(asset_str)
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

    def _on_error(self, error):
        self._logger.error('Got error msg %s', error)

    def close(self):
        """
        Send close message to server
        """
        if self.status != WebQuikConnector.Status.DISCONNECTING and self.Status != WebQuikConnector.Status.DISCONNECTED:
            self._logger.info("Disconnecting")
            self.status = WebQuikConnector.Status.DISCONNECTING
            self._ws.send('{"msgid":11016}')
            self._ws.close()

    def _on_close(self):
        self.status = WebQuikConnector.Status.DISCONNECTED
        self._logger.info('Disconnected')

    def subscribe(self, class_code, sec_code, subscriber: BaseFeed):
        """
        Subscribe to data for given security
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param subscriber subscriber class, inherited from base feed
        """
        key = (class_code, sec_code)

        # Register given feed callback
        self._feed_subscribers[key] = subscriber

        # Request this feed from server
        if self.status == WebQuikConnector.Status.CONNECTED:
            self._request_feed(class_code, sec_code)

    def _on_heartbeat(self, *args):
        """
        Pass heart beat event to subscribers
        """
        for subscriber in self._feed_subscribers.values():
            subscriber.on_heartbeat()
        self._heartbeat_cnt += 1
