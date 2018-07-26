import socket
import json
import logging
import sys


class QuikConnector:
    """
    Socket interactions with Quik: https://arqatech.com/en/products/quik/
    Quik side should have these Lua scripts installed:
    https://github.com/Arseniys1/QuikSocketTransfer
    """

    _MSG_ID_AUTH = 1
    _MSG_ID_CREATE_DATASOURCE = 2
    _MSG_ID_SET_UPDATE_CALLBACK = 3

    def __init__(self, host="192.168.1.104", port=1111, passwd='1'):
        """ Construct the class for host and port """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.host = host
        self.port = port
        self.passwd = passwd
        self.buf_size = 65536
        self.delimiter = 'message:'
        self.timeout_sec: float = 30.0
        self.sock: socket = None
        # Callbacks handlers for messages. One callback for one message id.
        self._callbacks = {self._MSG_ID_AUTH: self._on_auth
            , self._MSG_ID_CREATE_DATASOURCE: self._on_create_datasource
            , self._MSG_ID_SET_UPDATE_CALLBACK: self._on_set_update_callback
            , 'callback': self._on_update}

    def connect(self):
        """ Connect and authorize """
        self.logger.info("Connecting to " + self.host + ":" + str(self.port))
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self.logger.info("Connected to " + self.host + ":" + str(self.port))

    def auth(self):
        """ Authorize at Quik Lua """
        msg = '{ "id": %s , "method": "checkSecurity", "args": ["%s"] }' % (self._MSG_ID_AUTH, self.passwd)
        self.logger.debug('Sending message: %s' % msg)
        self.sock.sendall(bytes(msg, 'UTF-8'))

    def _on_auth(self, msg):
        """Authenticated event callback"""
        auth_result = msg['result'][0]
        self.logger.info('Auth result: %s' % auth_result)
        if not auth_result:
            raise ConnectionError("Quik LUA authentication failed")  # We got "authenticated Ok" message, exit auth loop
        # If authenticated, subscribe to data and receive it
        self._create_datasource()

    def _create_datasource(self):
        """
        Method from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        msg = '{"id": %s,"method": "CreateDataSource","args": ["SPBFUT", "SiU8", "INTERVAL_TICK"]}' % self._MSG_ID_CREATE_DATASOURCE
        self.logger.debug('Sending msg: %s' % msg)
        self.sock.sendall(bytes(msg, 'UTF-8'))

    def _on_create_datasource(self, msg):
        """
        Callback from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        datasource_id = msg['result'][0]
        self.logger.debug('Got msg: %s' % msg)
        self.logger.debug('Datasource id: %s' % datasource_id)
        self.set_update_callback(datasource_id)

    def set_update_callback(self, datasource_id):
        """
        Method from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        # Add this datasource id to callbacks
        self._callbacks[datasource_id] = self._on_update

        msg = '{"id": %s,"method": "SetUpdateCallback","args": [%s] }' % (
            self._MSG_ID_SET_UPDATE_CALLBACK, datasource_id)
        self.logger.debug('Sending msg: %s' % msg)
        self.sock.sendall(bytes(msg, 'UTF-8'))

    def _on_set_update_callback(self, msg):
        """
        Callback from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        self.logger.debug('Got set update callback responce. Msg: %s' % msg)
        result = msg['result'][0]
        self.logger.info('Result: %s' % result)
        if not result:
            raise Exception('Update callback not created.')

    def _on_update(self, msg):
        """
        Quotes receiver method.
        It is callback from subscription sequence: create_datasourdce, set_update_callback
        Callbacks: on_create_datasource, on_set_update_callback, on_update
        """
        self.logger.debug('Got callback msg: %s' % msg)
        ds_id = msg.get('ds_id')
        if not ds_id:
            self.logger.debug('No price data in the message')
            return
        self.logger.debug('Got data: %s' % msg['result'])

    def run(self):
        """ Connect and run message processing loop """
        self.connect()
        self.auth()

        # Message processing loo9p
        try:
            while True:
                data = self.sock.recv(self.buf_size).decode()
                self.logger.debug('Got data: %s' % data)
                data_items = data.split(self.delimiter)
                for data_item in data_items:
                    if not data_item:
                        continue  # Skip empty '' messages
                    # Parse single message
                    try:
                        msg: dict = json.loads(data_item)
                        self.logger.debug('Extracted message: %s' % str(msg))
                        # Call callback for this message
                        callback = self._callbacks.get(msg['id'])
                        if callback:
                            callback(msg)

                    except json.JSONDecodeError:
                        self.logger.error('Bad message: %s' % sys.exc_info())

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")

        # Exiting
        self.sock.close()
        self.logger.info('Socket closed')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    # execute only if run as a script
    QuikConnector().run()
