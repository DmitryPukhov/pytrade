import json
import logging
from enum import Enum
import websocket
from websocket import WebSocketApp
from connector.quik.MsgId import MsgId


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

    _HEARTBEAT_SECONDS = 3

    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, conn, account, passwd):
        # Create websocket, do not open and run here
        self._conn = conn
        self.websocket_app: WebSocketApp = websocket.WebSocketApp(self._conn,
                                                                  on_message=self._on_message,
                                                                  on_error=self._on_error,
                                                                  on_close=self._on_close,
                                                                  on_pong=self._on_heartbeat)
        self.websocket_app.on_open = self._on_socket_open
        self._passwd = passwd
        self._account = account
        self.status = self.Status.DISCONNECTED

        # Callbacks for different messages msgid
        # Socket callback self._on_message will call these
        self._callbacks = {
            MsgId.PIN_REQ: self._on_pin_req,
            MsgId.STATUS: self._on_status,
            MsgId.AUTH: self._on_auth,
            MsgId.TRADE_SESSION_OPEN: self._on_trade_session_open
        }
        # Broker and feed, subscribed to message id
        self._subscribers = {}

        # Heart beat support
        self._heartbeat_cnt = 0
        self.feed = None
        self.broker = None

    def start(self):
        """
        Create web socket and run loop
        """
        if self.status == WebQuikConnector.Status.DISCONNECTED:
            self.status = WebQuikConnector.Status.CONNECTING
            self._logger.info("Connecting to " + self._conn)
            # Run loop
            self.websocket_app.run_forever(ping_interval=self._HEARTBEAT_SECONDS)

    def send(self, msg: str):
        """
        Send message to web quik server, for example trade order or info request.
        """
        self._logger.info("Sending message: " + msg)
        self.websocket_app.send(msg)

    def _on_socket_open(self):
        """
        Socket on_open handler
        Login just after web socket has been opened
        """
        auth_msg = '{"msgid":10000,"login":"' + self._account + '","password":"' + self._passwd \
                   + '","width":"200","height":"200","userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
                     '(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36","lang":"ru",' \
                     '"sid":"144f9.2b851e74","version":"6.6.1"} '
        self.websocket_app.send(auth_msg)

    def _on_trade_session_open(self, msg):
        """
        Trade session is opened. Now we can request data and set orders
        """
        if msg['resultCode'] == 0:
            self._logger.info('Authenticated')
            self.status = WebQuikConnector.Status.CONNECTED
            self._logger.info('Connected. Trade session is opened')
            if self.feed:
                self.feed.on_trade_session_open(msg)
            if self.broker:
                self.broker.on_trade_session_open(msg)
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

    def _on_pin_req(self, msg):
        """
        On PIN request during auth. For some providers only.
        """
        pin_code = input("Enter sms pin code: ")
        pin_msg = '{"msgid":10001,"pin":"%s"}' % pin_code
        self.websocket_app.send(pin_msg)

    def _on_status(self, msg):
        """
        Connected event handler
        """
        connected_msg = '{"msgid":10008}'
        self.websocket_app.send(connected_msg)

    def _on_message(self, raw_msg):
        """
        Entry for message processing. Call specific processors for different messages.
        """
        strmsg = raw_msg.decode()
        # self._logger.debug('Got message %s', strmsg)
        msg = json.loads(strmsg)
        # Find and execute callback function for this message
        msgid = msg['msgid']
        self._logger.debug('Got message %s', msgid)

        # Call internal callback is set up
        msg_callback = self._callbacks.get(msgid)
        if msg_callback:
        # Don't send msg to consumers, process it in this class
            msg_callback(msg)

        # Call external callback: broker or feed subscriber
        for func in self._subscribers.setdefault(msgid,[]):
            func(msg)

    @staticmethod
    def asset2tuple(s):
        """
        Converts quik asset string to tuple(class, code)
        """
        # Split s and return first 2 parts - class and code
        parts: list = s.split("¦")
        return tuple([parts[0], parts[1]])

    @staticmethod
    def tuple2asset(t: tuple):
        """
        Converts asset tuple(class, code) to quik compatible string class¦code
        """
        return "%s¦%s" % (t[0], t[1])

    def _on_error(self, error):
        self._logger.error('Got error msg %s: %s', type(error).__name__, str(error))

    def close(self):
        """
        Send close message to server
        """
        if self.status != WebQuikConnector.Status.DISCONNECTING and self.Status != WebQuikConnector.Status.DISCONNECTED:
            self._logger.info("Disconnecting")
            self.status = WebQuikConnector.Status.DISCONNECTING
            self.websocket_app.send('{"msgid":11016}')
            self.websocket_app.close()

    def _on_close(self):
        self.status = WebQuikConnector.Status.DISCONNECTED
        self._logger.info('Disconnected')

    def _on_heartbeat(self, *args):
        """
        Pass heart beat event to subscribers
        """
        self._heartbeat_cnt += 1
        if self.feed is not None:
            self.feed.on_heartbeat()
        if self.broker is not None:
            self.broker.on_heartbeat()

    def subscribe(self, callbacks: {}):
        """
        Add message callback. Broker and feeder subscribe themselves to messages using this func.
        """
        for msgid in callbacks:
            self._subscribers.setdefault(msgid, []).append(callbacks[msgid])
