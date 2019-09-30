import logging
from pytrade.connector.quik.WebQuikConnector import WebQuikConnector


class QuikFeed:
    """
    Data feed facade for QuikConnector.
    Provides ticks data stream from quik
    """
    _logger = logging.getLogger(__name__)
    tick_callbacks = set()
    heartbeat_callbacks = set()

    def __init__(self, quik: WebQuikConnector, class_code, sec_code):
        """
        Constructor
        :param quik: QuikConnector instance
        :param class_code: sec class code, example 'SPBFUT'
        :param sec_code:  security name, example 'RIU8'
        """
        self._quik = quik
        self._quik.heartbeat_subscribers.add(self.on_heartbeat)
        self.class_code = class_code
        self.sec_code = sec_code
        # Subscribe to data stream
        self._quik.subscribe(self.class_code, self.sec_code, self.on_tick)

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """
        # Start quik connector loop
        self._logger.info("Starting quik data feed")
        if self._quik.status == WebQuikConnector.Status.DISCONNECTED:
            self._quik.run()

    def on_tick(self, class_code, sec_code, tick_time, price, vol):
        """
        Tick callback
        :param class_code security code, example 'SPBFUT'
        :param sec_code name of security, example 'RIU8'
        :param price: received price
        :param tick_time time
        :param vol: received volume
        :return: None
        """
        for callback in self.tick_callbacks:
            callback(class_code, sec_code, tick_time, price, vol)

    def on_heartbeat(self):
        """
        Listen heartbeat from connector and call subscribers
        """
        for callback in self.heartbeat_callbacks:
            callback()
