import json
import logging
import queue
import threading
from collections import defaultdict
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

    _HEARTBEAT_SECONDS = 10
    _TIMEOUT_SECONDS = 9

    def __new__(cls, *args, **kwargs):
        if not hasattr(WebQuikConnector, 'instance'):
            cls.instance = super(WebQuikConnector, cls).__new__(cls)
        return cls.instance

    #    def __init__(self, conn, account, passwd):
    def __init__(self, config):
        if getattr(self, 'is_initialized', False):
            return
        self.is_initialized = True
        self._conn = config["conn"]
        self._passwd = config["passwd"]
        self._account = config["account"]
        self._logger = logging.getLogger(__name__)

        # Create websocket, do not open and run here
        self.websocket_app: WebSocketApp = websocket.WebSocketApp(self._conn,
                                                                  header={
                                                                      "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                                                                    "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
                                                                      "sid": "144f9.2b851e74",
                                                                      "version": "6.6.1"
                                                                  },
                                                                  on_message=self._on_socket_message,
                                                                  on_error=self._on_error,
                                                                  on_close=self._on_close,
                                                                  on_pong=self._on_socket_heartbeat)
        self.websocket_app.on_open = self._on_socket_open
        self.status = self.Status.DISCONNECTED

        # Callbacks for different messages msgid
        # Socket callback self._on_message will call these
        self._callbacks = {
            MsgId.PIN_REQ: self._on_pin_req,
            MsgId.STATUS: self._on_status,
            MsgId.AUTH: self._on_auth,
            MsgId.TRADE_SESSION_OPEN: self._on_trade_session_open,

            # Reply messages
            MsgId.SERVER_MSG: self._on_msg_reply,
            MsgId.REMOVE_STOP_ORDER_REPLY: self._on_msg_reply,
            MsgId.REMOVE_ORDER_REPLY: self._on_msg_reply,
            MsgId.ORDER_REPLY: self._on_msg_reply,
            MsgId.STOP_ORDER_REPLY: self._on_msg_reply,
            MsgId.LINKED_STOP_ORDER_REPLY: self._on_msg_reply,
            MsgId.FX_ORDER_REPLY: self._on_msg_reply,
            MsgId.CONDITIONAL_STOP_ORDER_REPLY: self._on_msg_reply,
            MsgId.TRANS_REPLY: self._on_msg_reply,
            MsgId.HEARTBEAT: self._on_heartbeat
        }
        # Broker and feed, subscribed to message id
        self._subscribers = defaultdict(list)
        self._msgqueue: queue.Queue = queue.Queue()
        self._heartbeat_cnt = 0
        self._last_heartbeat = 0
        self._is_run = False

    def run_once(self):
        """
        Run or skip if already called
        """
        if self._is_run:
            return
        self._is_run = True
        threading.Thread(target=self.run_socket_app).start()
        self.run_msg_loop()

    def run_socket_app(self):
        """
        Create web socket and run loop
        """
        self._logger.info("Running socket app")
        if self.status == WebQuikConnector.Status.DISCONNECTED:
            self.status = WebQuikConnector.Status.CONNECTING
            self._logger.info("Connecting to " + self._conn)
            # Run loop
            self.websocket_app.run_forever(ping_interval=self._HEARTBEAT_SECONDS)

    def send(self, msg: str):
        """
        Send message to web quik server, for example trade order or info request.
        """
        self._logger.debug("Sending message: " + msg)
        self.websocket_app.send(msg)

    def _on_socket_open(self, src):
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

    def _on_socket_message(self, src, raw_msg):
        """
        Get message from socket and put into the queue
        """
        # Queue is thread-safe already
        self._msgqueue.put(raw_msg)

    def _on_socket_heartbeat(self, *args):
        """
        Get pong event from socket
        """

        msg = json.dumps({"msgid": MsgId.HEARTBEAT})
        self._msgqueue.put(msg.encode())
        self._heartbeat_cnt += 1

    def run_msg_loop(self):
        """
        Main messages processing loop
        Socket thread reads messages from socket and pushes to the queue
        This msg_loop function runs in another thread, it pops messages from the queue and processes them
        """
        self._logger.info("Starting messages loop")
        while True:
            # get() method waits for the item then retuns it, using thread.Lock inside.
            msg = self._msgqueue.get()
            self._on_message(msg)
        self._logger.info("End messages loop")

    def _on_message(self, raw_msg):
        """
        Entry for message processing. Call specific processors for different messages.
        """
        try:
            strmsg = raw_msg.decode()
            self._logger.debug('Got message %s', strmsg[:200])
            msg = json.loads(strmsg)
            # Find and execute callback function for this message
            msgid = msg['msgid']

            # Call internal callback is set up
            msg_callback = self._callbacks.get(msgid)
            if msg_callback:
                # Don't send msg to consumers, process it in this class
                msg_callback(msg)

            # Call external callback: broker or feed subscriber
            for func in self._subscribers[msgid]:
                func(msg)
        except Exception as e:
            self._logger.exception(f"{e}, msg:{raw_msg.decode()}")

    def _on_msg_reply(self, msg):
        for func in self._subscribers[msg['msgid']]:
            func(msg)

    def _on_error(self, src, error):
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

    def _on_close(self, src, p1, p2):
        self._logger.info(f"Got on_close event:{src}, {p1},{p2}")
        if self.status == WebQuikConnector.Status.DISCONNECTING:
            # If it's me who closed the socket
            self.status = WebQuikConnector.Status.DISCONNECTED
            self._logger.info('Disconnected')
        else:
            # Reconnect if closed itself without my wish
            self._logger.info('The socket unexpectedly closed, reconnecting...')
            self.websocket_app.close()
            self.status = WebQuikConnector.Status.DISCONNECTED
            self.run()

    def _on_heartbeat(self, *args):
        """
        Pass heart beat event to subscribers
        """
        self._logger.debug(f"Got heart beat. msg queue size: {self._msgqueue.qsize()}")

    def subscribe(self, callbacks: {}):
        """
        Add message callback. Broker and feeder subscribe themselves to messages using this func.
        """
        for msgid in callbacks:
            self._subscribers.setdefault(msgid, []).append(callbacks[msgid])
