import json
import logging
from datetime import datetime
from enum import Enum
import websocket
from websocket import WebSocketApp, ABNF


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
                           self._MSG_ID_DATA: self._on_data
                           }

        # Subscribers for data feed
        self._feed_subscribers = {}
        # Broker information subscribers
        self.broker_subscribers = []
        # Heart beat support
        self.heartbeat_subscribers = set()
        self._heartbeat_cnt = 0

    def run(self):
        """
        Create web socket and run loop
        """
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
        Request data from quik
        """
        # Request quotes
        self._logger.info('Requesting quotes for %s\\%s', class_code, sec_code)
        msg = '{"msgid":%s,"c":"%s","s":"%s","p":%s}' % (self._MSG_ID_CREATE_DATASOURCE, class_code, sec_code, 15)
        msg = msg.encode()
        self._logger.debug('Sending msg: %s' % msg)
        self._ws.send(msg)
        # Request level2 data
        self._logger.info('Requesting level2 data for %s\\%s', class_code, sec_code)
        msg = '{"msgid":%s,"c":"%s","s":"%s","depth":%s}' % \
              (self._MSG_ID_CREATE_LEVEL2_DATASOURCE, class_code, sec_code, 30)
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

    def _on_data(self, data: dict):
        """
        Process message with level1 or level2 data
        Received msg with data. Msg can contain bid, ask, last fields
        :param data: dictionary like
            {"msgid":21011,"dataResult":{"CETS\u00A6EUR_RUB__TOM":{"last":70.74,"lastchange":-0.01,"offer":70.7375}}}
        """

        # Conversions of class, asset in data
        def str2tuple(s):
            return tuple(s.split("¦"))

        def tuple2str(t):
            return "%s¦%s" % (t[0], t[1])

        # Find assets who has subscribers
        data_result = dict(data['dataResult'])
        all_feeds_encoded = set(map(tuple2str, self._feed_subscribers.keys()))
        feeds_encoded = set(data_result.keys()).intersection(all_feeds_encoded)

        for asset_encoded in feeds_encoded:
            # Time not come from quik server
            tick_time = datetime.now()
            asset = str2tuple(asset_encoded)
            price = data_result[asset_encoded].get('last')
            if price is not None:
                # If it is level1 message, send it to tick feed
                self._feed_subscribers[asset](asset[0], asset[1], tick_time, price, 0)
            # todo: implement level2 feed

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

    def subscribe(self, class_code, sec_code, feed_callback):
        """
        Subscribe to data for given security
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param feed_callback callback function to pass price/volume into
        """
        # Register given feed callback
        self._feed_subscribers[(class_code, sec_code)] = feed_callback
        # Request this feed from server
        if self.status == WebQuikConnector.Status.CONNECTED:
            self._request_feed(class_code, sec_code)

    def _on_heartbeat(self, *args):
        for callback in self.heartbeat_subscribers:
            callback()
        self._heartbeat_cnt += 1
