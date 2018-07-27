import socket
import json
import logging
import sys
from logging import Logger


class QuikConnector:
    """
    Socket interactions with Quik: https://arqatech.com/en/products/quik/
    Quik side should have these Lua scripts installed:
    https://github.com/Arseniys1/QuikSocketTransfer
    """
    _delimiter: str = 'message:'
    _buf_size: int = 65536
    _sock: socket = None
    _logger: Logger = None

    _MSG_ID_AUTH = 'msg_auth'
    _MSG_ID_CREATE_DATASOURCE = 'msg_create_ds'
    _MSG_ID_SET_UPDATE_CALLBACK = 'msg_set_upd_callback'

    # Mapping datasource id -> security code, like 1 - SBER
    # datasource id comes from quik lua, it's integer. Need to know which instrument is it
    _sec_code_by_ds_id = {}

    def __init__(self, host="192.168.1.104", port=1111, passwd='1'):
        """ Construct the class for host and port """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        self._host = host
        self._port = port
        self._passwd = passwd
        self._sock: socket = None

        # Callbacks handlers for messages. One callback for one message id.
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth,
                           self._MSG_ID_CREATE_DATASOURCE: self._on_create_datasource,
                           self._MSG_ID_SET_UPDATE_CALLBACK: self._on_set_update_callback,
                           'callback': self._on_data}

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
        self._logger.info('Auth result: %s' % auth_result)
        if not auth_result:
            raise ConnectionError("Quik LUA authentication failed")  # We got "authenticated Ok" message, exit auth loop
        # If authenticated, subscribe to data and receive it
        self._create_datasource('SBER')

    def _create_datasource(self, sec_code):
        """
        Method from subscription sequence: create_datasource, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        # msg = '{"id": %s,"method": "CreateDataSource","args": ["SPBFUT", "SiU8", "INTERVAL_TICK"]}' \
        msg_id = '%s_%s' % (self._MSG_ID_CREATE_DATASOURCE, sec_code)
        msg = '{"id": "%s","method": "CreateDataSource","args": ["TQBR", "%s", "INTERVAL_TICK"]}' \
              % (msg_id, sec_code)
        self._callbacks[msg_id] = self._on_create_datasource
        self._logger.info('Sending msg: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_create_datasource(self, msg):
        """
        Callback from subscription sequence: create_datasource, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        self._logger.info('Got msg: %s' % msg)

        # Update ds id -> security code map
        msg_id = msg['id']
        datasource_id = msg['result'][0]
        self._sec_code_by_ds_id[datasource_id] = msg_id

        self._set_update_callback(datasource_id)

    def _set_update_callback(self, datasource_id):
        """
        Method from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        msg = '{"id": "%s","method": "SetUpdateCallback","args": ["%s"] }' % (
            self._MSG_ID_SET_UPDATE_CALLBACK, datasource_id)
        self._logger.info('Sending msg: %s' % msg)
        self._sock.sendall(bytes(msg, 'UTF-8'))

    def _on_set_update_callback(self, msg):
        """
        Callback from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        self._logger.info('Got set update callback responce. Msg: %s' % msg)
        result = msg['result'][0]
        self._logger.info('Result: %s' % result)
        if not result:
            raise Exception('Update callback not created.')

    def _on_data(self, msg):
        """
        Quotes receiver method.
        It is callback from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        self._logger.debug('Got callback msg: %s' % msg)
        ds_id = msg.get('ds_id')
        if not ds_id:
            self._logger.debug('No price data in the message')
            return
        sec_code = self._sec_code_by_ds_id.get(ds_id)
        value = msg.get('result')
        if not sec_code:
            self._logger.debug('Unknown data source id %s', ds_id)
            return

        self._logger.info('Got ds_id: %s, security code: %s, value: %s' % (ds_id, sec_code, value))

    def run(self):
        """ Connect and run message processing loop """
        self._connect()
        self._auth()

        # Message processing loop
        try:
            while True:
                data = self._sock.recv(self._buf_size).decode()
                self._logger.debug('Got packet: %s' % data)
                data_items = data.split(self._delimiter)
                for data_item in data_items:
                    if not data_item:
                        continue  # Skip empty '' messages
                    # Parse single message
                    try:
                        msg: dict = json.loads(data_item)
                        self._logger.debug('Extracted message: %s' % str(msg))
                        # Call callback for this message
                        callback = self._callbacks.get(msg['id'])
                        if callback:
                            callback(msg)

                    except json.decoder.JSONDecodeError:
                        self._logger.exception('Bad message')

        except KeyboardInterrupt:
            self._logger.info("Interrupted by user")

        # Exiting
        self._sock.close()
        self._logger.info('Socket closed')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    # execute only if run as a script
    QuikConnector().run()
