import json
import logging
import socket
from enum import Enum
import datetime as dt
import time


class QuikConnector:
    """
    Socket interactions with Quik: https://arqatech.com/en/products/quik/
    Quik side should have these Lua scripts installed:
    https://github.com/Arseniys1/QuikSocketTransfer
    """

    class Status(Enum):
        DISCONNECTED = 0
        CONNECTING = 1
        CONNECTED = 3
        BUSY = 4

    _MSG_ID_AUTH = 'msg_auth'
    _MSG_ID_CREATE_DATASOURCE = 'msg_create_ds'
    _MSG_ID_SET_UPDATE_CALLBACK = 'msg_set_upd_callback'
    _MSG_DELIMITER = 'message:'
    _MSG_ID_GET_POS = 'msg_get_pos'
    _HEARTBEAT_SECONDS = 3

    _buf_size = 65536
    _logger = logging.getLogger(__name__)

    # msg_encoding = 'UTF-8'
    msg_encoding = '1251'  # Quik sends messages in 1251 encoding.

    def __init__(self, host="192.168.1.104", port=1111, passwd='1', account='SPBFUT00998'):
        self._logger.setLevel(logging.INFO)
        self._host = host
        self._port = port
        self._passwd = passwd
        self._sock = None
        self._account = account
        self._last_trans_id = 0
        self.status = self.Status.DISCONNECTED

        # Callbacks handlers for messages. One callback for one message id.
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth,
                           self._MSG_ID_CREATE_DATASOURCE: self._on_create_datasource,
                           # self._MSG_ID_SET_UPDATE_CALLBACK: self._on_set_update_callback,
                           'callback': self._callback}

        # Subscribers for data feed
        self._feed_callbacks = {}
        # Broker information subscribers
        self.broker_callbacks = []

        # Callback functions for each tick, when any new message received
        self.heartbeat_callbacks = set()
        self._last_heartbeat = 0

    def _connect_sock(self):
        """
        Connect and authorize. Synchronous operation.
        """
        self.status = QuikConnector.Status.CONNECTING
        self._logger.info("Connecting to " + self._host + ":" + str(self._port))
        self._sock = socket.socket()
        self._sock.connect((self._host, self._port))
        self._logger.info("Connected to " + self._host + ":" + str(self._port))

    def _auth(self):
        """
        Authorize at Quik Lua. Asynchronous operation
        """
        msg = '{ "id": "%s" , "method": "checkSecurity", "args": ["%s"] }' % (self._MSG_ID_AUTH, self._passwd)
        self._logger.info("Authorizing.")
        self._logger.debug('Sending authorizing message: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_auth(self, msg):
        """
        Authenticated event callback
        """
        auth_result = msg['result'][0]
        if not auth_result:
            raise ConnectionError("Quik LUA authentication failed")
        self.status = QuikConnector.Status.CONNECTED
        self._logger.info('Authorized')
        self._create_subscribers_datasources()
        # If authenticated, subscribe to data
        # self._create_datasource(self.sec_code)
        # Send order 4 test
        # todo: remove this test code
        # self._send_order(class_code='SPBFUT', sec_code='RIU8', quantity=1)

    def subscribe(self, class_code, sec_code, feed_callback):
        """
        Subscribe to data for given security
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param feed_callback callback function to pass price/volume into
        """
        self._feed_callbacks[(class_code, sec_code)] = feed_callback
        if self.status == QuikConnector.Status.CONNECTED:
            self._create_datasource(class_code, sec_code)

    def _create_subscribers_datasources(self):
        """
        Call _create_datasource for every security from feed_callbacks
        feed_callback already contains map (class_code, sec_code): feed callback function
        :return: None
        """
        for (class_code, sec_code), value in self._feed_callbacks.items():
            self._create_datasource(class_code, sec_code)

    def _create_datasource(self, class_code, sec_code):
        """
        After CreateDataSource method call we'll receive OnAllTrade messages
        """
        msg_id = '%s_%s_%s' % (self._MSG_ID_CREATE_DATASOURCE, class_code, sec_code)
        msg = '%s{"id": "%s","method": "CreateDataSource","args": ["%s", "%s", "INTERVAL_TICK"]}' \
              % (self._MSG_DELIMITER, msg_id, class_code, sec_code)
        self._logger.info('Sending msg: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_create_datasource(self, msg):
        """
        Log created data source id or error message
        """
        # Result contain data source id or error text. Print it to log
        datasource_id = msg['result'][0]
        self._logger.info('Created datasource id: %s' % datasource_id)

    def _callback(self, msg):
        """
        Process callback message, actually call price_vol or transaction callback.
        :param msg: message, decoded from json as dict
        :return: None
        """
        # Redirect to more specific callback
        switcher = {'OnAllTrade': self._on_all_trade,
                    'OnTransReply': self._on_trans_reply}
        func = switcher.get(msg['callback_name'])
        if func is None:
            return
        func(msg)

    def _on_trans_reply(self, msg):
        """
        Transaction callback
        """
        result = msg['result']
        if type(result) is dict:
            # This OnTransReply is what we needed. It contains the responce to our transaction.
            self._logger.info(msg['result']['result_msg'])
        else:
            # Quik sends first OnTransReply when message is received ?
            self._logger.info('Result: %s' % msg['result'])

    def _on_order_reply(self, msg):
        """
        Order reply callback. We have 2 callbacks to order:
        - with msg_id=OnTransReply result=[return code]
        - with msg_id=<sent order id>  result=[ return message ] (this)
        This callback is more informative in case of error, we catch it and write to log
        :param msg:
        :return:
        """
        self._logger.info('Order callback. order id: %s, result: %s' % (msg['id'], msg['result']))

    def _on_all_trade(self, msg):
        """
        price/vol callback - new tick came to us
        The most important method in all the connector: processes received price/vol data
        :param msg: message from quik, already decoded to a dictionary
        :return: None
        """

        if msg['callback_name'] != 'OnAllTrade':
            return
        result = msg['result']
        class_code = result['class_code']
        sec_code = result['sec_code']
        callback = self._feed_callbacks.get((class_code, sec_code))
        if callback is not None:
            self._logger.debug('Feed callback found for class_code=%s, sec_code=%s' % (class_code, sec_code))

            res_dt = result['datetime']
            tick_time = dt.datetime(res_dt['year'], res_dt['month'], res_dt['day'], res_dt['hour'], res_dt['min'],
                                    res_dt['sec'], res_dt['ms'])

            callback(class_code, sec_code, tick_time, result['price'], result['qty'])

    def send_order(self, class_code, sec_code, operation, price, quantity):
        """
        Buy/sell order
        :param type 'L' for limit
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :param operation B for buy, S for sell
        :param price for limit order. For market order set price to 0
        :param stop_price stop loss
        :param tra_stop_price trailing stop
        :param quantity number of items to buy/sell
        :return:
        """
        self._last_trans_id += 1
        # if stop_price is not None and stop_price != 0:
        #     suffix = 'ACTION=NEW_STOP_ORDER\\nSTOPPRICE=%s' % (stop_price)
        # else:
        #     suffix = 'ACTION=NEW_ORDER'
        trans = 'ACTION=NEW_ORDER\\nACCOUNT=%s\\nCLIENT_CODE=%s\\nTYPE=L\\nTRANS_ID=%d\\nCLASSCODE=%s\\nSECCODE=%s\\nOPERATION=%s\\nPRICE=%s\\nQUANTITY=%d' \
                % (self._account, self._account, self._last_trans_id, class_code, sec_code, operation, price, quantity)
        self._logger.info('Sending order: %s' % trans)
        # Send
        self._send_order_msg(trans)

    def _send_order_msg(self, trans):
        """
        Send transaction message, subscribe to responce on result of this transaction
        :param trans prepared transaction string for quik
        :return None
        """

        order_msg = '%s{"id": "order_%s","method": "sendTransaction","args": ["%s"]}' % (
            self._MSG_DELIMITER, self._last_trans_id, trans)
        self._logger.info('Sending order %s' % order_msg)
        # Send order
        self._sock.sendall(bytes(order_msg, 'UTF-8'))

        # Send reply req
        trans_reply_id = str(self._last_trans_id) + '_reply'
        trans_reply_msg = '%s{"id": "%s","method": "OnTransReply","args": ["%s"]}' \
                          % (self._MSG_DELIMITER, trans_reply_id, self._last_trans_id)
        self._sock.sendall(bytes(trans_reply_msg, 'UTF-8'))

    def run(self):
        """
         Run message processing loop
         Should be already connected
        """

        # Connecting
        self._connect_sock()
        self._auth()

        # Message processing loop
        try:
            while True:
                data = self._sock.recv(self._buf_size)
                try:
                    data = data.decode(self.msg_encoding)
                    self._logger.debug(data)
                    # Received data can contain multiple messages
                    data_items = data.split(self._MSG_DELIMITER)

                    for data_item in data_items:
                        if not data_item:
                            continue  # Skip empty '' messages
                        # Parse single message
                        try:
                            msg = json.loads(data_item)
                            msg_id = msg['id']

                            # Call callback for this message
                            callback = self._callbacks.get(msg_id)
                            if callback:
                                callback(msg)
                            else:
                                # Order reply id should start from 'order'
                                if str(msg_id).startswith('order'):
                                    self._on_order_reply(msg)

                        except json.decoder.JSONDecodeError:
                            self._logger.exception('Bad message packet %s, message %s' % (data, data_item))
                except UnicodeDecodeError:
                    self._logger.exception('Bad message packet %s' % data)

                # Do heartbeat when connected to quik
                if self.status == QuikConnector.Status.CONNECTED \
                        and time.time() - self._last_heartbeat > self._HEARTBEAT_SECONDS:
                    self._last_heartbeat = time.time()
                    for callback in self.heartbeat_callbacks:
                        callback()

        except KeyboardInterrupt:
            self._logger.info("Interrupted by user")

        # Exiting
        self.status = QuikConnector.Status.DISCONNECTED
        self._sock.close()
        self._logger.info('Disconnected')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    # execute only if run as a script
    # QuikConnector().run()
