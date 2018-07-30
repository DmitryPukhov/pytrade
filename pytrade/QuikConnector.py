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
    _MSG_ID_AUTH = 'msg_auth'
    _MSG_ID_CREATE_DATASOURCE = 'msg_create_ds'
    _MSG_ID_SET_UPDATE_CALLBACK = 'msg_set_upd_callback'

    _delimiter: str = 'message:'
    _buf_size: int = 65536
    _sock: socket = None
    _logger: Logger = None
    _connected = False

    # Main security to get price/vol of
    sec_code = None

    def __init__(self, host="192.168.1.104", port=1111, passwd='1'):
        """ Construct the class for host and port """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        self._host = host
        self._port = port
        self._passwd = passwd
        self._sock: socket = None
        self.sec_code = 'RIU8'

        # Callbacks handlers for messages. One callback for one message id.
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth,
                           self._MSG_ID_CREATE_DATASOURCE: self._on_create_datasource,
                           # self._MSG_ID_SET_UPDATE_CALLBACK: self._on_set_update_callback,
                           'callback': self._callback}

    def _connect(self):
        """ Connect and authorize """
        self._logger.info("Connecting to " + self._host + ":" + str(self._port))
        self._sock = socket.socket()
        self._sock.connect((self._host, self._port))
        self._logger.info("Connected to " + self._host + ":" + str(self._port))

    def _auth(self):
        """ Authorize at Quik Lua """
        msg = '{ "id": "%s" , "method": "checkSecurity", "args": ["%s"] }' % (self._MSG_ID_AUTH, self._passwd)
        self._logger.debug('Sending message: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_auth(self, msg):
        """Authenticated event callback"""
        auth_result = msg['result'][0]
        if not auth_result:
            raise ConnectionError("Quik LUA authentication failed")
        self._connected = True
        self._logger.info('Connected')

        # If authenticated, subscribe to data
        self._create_datasource(self.sec_code)

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
        The most important method in all the connector: processes received price/vol data
        :param msg: message from quik, already decoded to a dictionary
        :return: None
        """
        # We need ensure first that this message contains our security with it's price/volume
        if msg['callback_name'] != 'OnAllTrade' or msg['result']['sec_code'] != self.sec_code:
            return
        # It is really our price/volume, get them
        price = msg['result']['price']
        vol = msg['result']['qty']
        self._logger.info('%s price: %s, volume: %s' % (self.sec_code, price, vol))

    def run(self):
        """ Connect and run message processing loop """

        # Connecting
        self._connect()
        self._auth()

        # Message processing loop
        try:
            while True:
                data = self._sock.recv(self._buf_size).decode()
                # Received data can contain multiple messages
                data_items = data.split(self._delimiter)
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
