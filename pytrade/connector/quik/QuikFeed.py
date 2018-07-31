from pytrade.connector.quik.QuikConnector import  QuikConnector
import logging


class QuikFeed:
    """
    Data feed facade for QuikConnector.
    Provides ticks data stream from quik
    """

    _logger = logging.getLogger(__name__)

    def __init__(self, quik):
        self.quik = quik

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """

        self._logger.info("Starting quik data feed")
        if self.quik.status == QuikConnector.Status.DISCONNECTED:
            self.quik.run()
