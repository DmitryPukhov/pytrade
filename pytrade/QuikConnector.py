import socket
import json
import logging
import time
import sys


class QuikConnector(object):
    """
    Socket interactions with Quik: https://arqatech.com/en/products/quik/
    Quik side should have these Lua scripts installed:
    https://github.com/Arseniys1/QuikSocketTransfer
    """
    buf_size = 65536
    delimiter = 'message:'
    timeout_sec: float = 30.0
    sock: socket = None

    def __init__(self, host="192.168.1.104", port=1111, passwd='1'):
        """ Construct the class for host and port """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.host = host
        self.port = port
        self.passwd = passwd

    def connect(self):
        """ Connect and authorize """

        self.logger.info("Connecting to " + self.host + ":" + str(self.port))
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        self.logger.info("Connected to " + self.host + ":" + str(self.port))

        # Authenticate
        self.auth()

    def auth(self):
        """ Authorize at Quik Lua """

        # Authorize
        auth_msg_id: int = 1
        msg = '{ "id": %s , "method": "checkSecurity", "args": ["%s"] }' % (auth_msg_id, self.passwd)
        self.sock.sendall(bytes(msg, 'UTF-8'))
        auth_result: bool = None

        # Auth loop: receive rubbish messages until we get result of our login attempt
        time_end: float = time.time() + self.timeout_sec
        while not auth_result:
            if time.time() > time_end:
                raise TimeoutError('Timeout %s' % self.timeout_sec)

            data = self.sock.recv(self.buf_size).decode()
            self.logger.debug('Got data: %s' % data)
            if not data:
                continue
            # We can receive multiple messages with 'message:' delimiter
            data_items = data.split(self.delimiter)
            for data_item in data_items:
                if not data_item:
                    continue  # Skip empty '' messages
                msg = json.loads(data_item)
                self.logger.debug("Extracted message: " + str(msg))
                if msg['id'] == auth_msg_id:
                    auth_result = msg['result'][0]
                    self.logger.info('Auth result: %s' % auth_result)
                    # We got "authenticated Ok" message, exit auth loop
                    break
            if not auth_result:
                self.sock.close()
                raise ConnectionError("Quik LUA authentication failed")
        self.logger.info("Authenticated at " + self.host + ":" + str(self.port))

    def run(self):
        """ Connect and run message processing loop """

        self.connect()

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
                        msg: object = json.loads(data_item)
                        self.logger.debug('Extracted message: %s' % str(msg))
                    except json.JSONDecodeError:
                        self.logger.error('Bad message: %s' % sys.exc_info())
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")

        self.sock.close()
        self.logger.info('Socket closed')


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    # execute only if run as a script
    QuikConnector().run()
