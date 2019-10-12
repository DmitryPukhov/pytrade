import logging
from pytrade.connector.quik.WebQuikConnector import WebQuikConnector


class QuikFeed:
    """
    Data feed facade for QuikConnector.
    Provides price and level2 data stream from quik for specific assets.
    """
    _logger = logging.getLogger(__name__)
    feed_callbacks = set()
    level2_callbacks = set()
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
        self._quik.subscribe(self.class_code, self.sec_code, self.on_feed, self.on_level2)

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """
        # Start quik connector loop
        self._logger.info("Starting quik data feed")
        if self._quik.status == WebQuikConnector.Status.DISCONNECTED:
            self._quik.run()

    def on_feed(self, class_code, sec_code, dt, o, h, l, c, v):
        """
        Price data
        """
        for callback in self.feed_callbacks:
            callback(class_code, sec_code, dt, o, h, l, c, v)

    def on_level2(self):
        for callback in self.level2_callbacks:
            callback()

    def on_heartbeat(self):
        """
        Listen heartbeat from connector and call subscribers
        """
        for callback in self.heartbeat_callbacks:
            callback()
