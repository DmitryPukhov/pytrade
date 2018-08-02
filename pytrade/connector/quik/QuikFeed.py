from pytrade.connector.quik.QuikConnector import  QuikConnector
import logging


class QuikFeed:
    """
    Data feed facade for QuikConnector.
    Provides ticks data stream from quik
    """

    _logger = logging.getLogger(__name__)
    callbacks = set()

    def __init__(self, quik, class_code, sec_code):
        """
        Constructor
        :param quik: QuikConnector instance
        :param sec_code: security code, example 'SPBFUT'
        :param sec_name:  security name, example 'RIU8'
        """
        self._quik = quik
        self.class_code = class_code
        self.sec_code = sec_code

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """

        # Subscribe to data stream
        self._quik.subscribe(self.class_code, self.sec_code, self.on_tick)

        # Start quik connector loop
        self._logger.info("Starting quik data feed")
        if self._quik.status == QuikConnector.Status.DISCONNECTED:
            self._quik.run()

    def on_tick(self, sec_code, sec_name, price, vol):
        """
        Tick callback
        :param sec_code security code, example 'SPBFUT'
        :param sec_name name of security, example 'RIU8'
        :param price: received price
        :param vol: received volume
        :return: None
        """
        for callback in self.callbacks:
            callback(sec_code, sec_name, price, vol)