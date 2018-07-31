import json
import logging
import socket
from logging import Logger


class QuikConnector:
    """
    Socket interactions with Quik: https://arqatech.com/en/products/quik/
    Quik side should have these Lua scripts installed:
    https://github.com/Arseniys1/QuikSocketTransfer
    """
    _logger = logging.getLogger(__name__)
    _MSG_ID_AUTH = 'msg_auth'
    _MSG_ID_CREATE_DATASOURCE = 'msg_create_ds'
    _MSG_ID_SET_UPDATE_CALLBACK = 'msg_set_upd_callback'
    _MSG_DELIMITER: str = 'message:'
    _buf_size: int = 65536
    # msg_encoding = 'UTF-8'
    msg_encoding = '1251'  # Quik sends messages in 1251 encoding.

    def __init__(self, host="192.168.1.104", port=1111, passwd='1', account='SPBFUT00998'):
        self._logger.setLevel(logging.DEBUG)
        self._host = host
        self._port = port
        self._passwd = passwd
        self._sock: socket = None
        self._account = account
        self._last_trans_id = 0
        self.sec_code = 'RIU8'

        # Callbacks handlers for messages. One callback for one message id.
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth,
                           self._MSG_ID_CREATE_DATASOURCE: self._on_create_datasource,
                           # self._MSG_ID_SET_UPDATE_CALLBACK: self._on_set_update_callback,
                           'callback': self._callback}

    def _connect(self):
        """
        Connect and authorize
        """
        self._logger.info("Connecting to " + self._host + ":" + str(self._port))
        self._sock = socket.socket()
        self._sock.connect((self._host, self._port))
        self._logger.info("Connected to " + self._host + ":" + str(self._port))

    def _auth(self):
        """
        Authorize at Quik Lua
        """
        msg = '{ "id": "%s" , "method": "checkSecurity", "args": ["%s"] }' % (self._MSG_ID_AUTH, self._passwd)
        self._logger.debug('Sending message: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_auth(self, msg):
        """
        Authenticated event callback
        """
        auth_result = msg['result'][0]
        if not auth_result:
            raise ConnectionError("Quik LUA authentication failed")
        self._connected = True
        self._logger.info('Connected')
        # If authenticated, subscribe to data
        # self._create_datasource(self.sec_code)
        # Send order 4 test
        # todo: remove this test code
        self._send_order(classcode='SPBFUT', seccode='RIU8', quantity=1)

    def _create_datasource(self, sec_code):
        """
        After CreateDataSource method call we'll receive OnAllTrade messages
        """
        msg_id = '%s_%s' % (self._MSG_ID_CREATE_DATASOURCE, sec_code)
        msg = '{"id": "%s","method": "CreateDataSource","args": ["SPBFUT", "%s", "INTERVAL_TICK"]}' \
              % (msg_id, sec_code)
        self._logger.info('Sending msg: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_create_datasource(self, msg):
        """
        Log created data source id or error message
        """
        # Result contain data sourc id or error text. Print it to log
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

    def _on_all_trade(self, msg):
        """
        price/vol callback
        The most important method in all the connector: processes received price/vol data
        :param msg: message from quik, already decoded to a dictionary
        :return: None
        """

        if msg['callback_name'] != 'OnAllTrade' or msg['result']['sec_code'] != self.sec_code:
            return
        price = msg['result']['price']
        vol = msg['result']['qty']
        self._logger.info('%s price: %s, volume: %s' % (self.sec_code, price, vol))

    def _send_order(self, classcode, seccode, quantity=1):
        """
        Buy/sell order
        :return:
        """
        self._last_trans_id += 1
        ## !!! Works!!!
        # trans = 'ACCOUNT=SPBFUT00998\\nCLIENT_CODE=SPBFUT00998\\nTYPE=L\\nTRANS_ID=%d\\nCLASSCODE=SPBFUT\\nSECCODE=RIU8\\nACTION=NEW_ORDER\\nOPERATION=B\\nPRICE=0\\nQUANTITY=1'% trans_id
        # trans = 'ACCOUNT=SPBFUT00998\\nCLIENT_CODE=SPBFUT00998\\nTYPE=L\\nTRANS_ID=%d\\nCLASSCODE=SPBFUT\\nSECCODE=RIU8\\nACTION=NEW_ORDER\\nOPERATION=S\\nPRICE=0\\nQUANTITY=1'% trans_id

        trans = 'ACCOUNT=%s\\nCLIENT_CODE=%s\\nTYPE=L\\nTRANS_ID=%d\\nCLASSCODE=%s\\nSECCODE=%s\\nACTION=NEW_ORDER\\nOPERATION=B\\nPRICE=0\\nQUANTITY=%d' \
                % (self._account, self._account, self._last_trans_id, classcode, seccode, quantity)
        order_msg = '%s{"id": "%s","method": "sendTransaction","args": ["%s"]}' % (
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
         Connect and run message processing loop
          """

        # Connecting
        self._connect()
        self._auth()

        # Message processing loop
        try:
            while True:
                data = self._sock.recv(self._buf_size)
                try:
                    data = data.decode(self.msg_encoding)
                    print(data)
                    # Received data can contain multiple messages
                    data_items = data.split(self._MSG_DELIMITER)

                    for data_item in data_items:
                        if not data_item:
                            continue  # Skip empty '' messages
                        # Parse single message
                        try:
                            msg: dict = json.loads(data_item)
                            # Call callback for this message
                            callback = self._callbacks.get(msg['id'])
                            if callback:
                                callback(msg)
                        except json.decoder.JSONDecodeError:
                            self._logger.exception('Bad message packet %s, message %s' % (data, data_item))
                except UnicodeDecodeError:
                    self._logger.exception('Bad message packet %s' % data)
        except KeyboardInterrupt:
            self._logger.info("Interrupted by user")

        # Exiting
        self._connected = False
        self._sock.close()
        self._logger.info('Disconnected')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    # execute only if run as a script
    QuikConnector().run()
