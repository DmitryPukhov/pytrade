from pytrade.connector.quik.QuikConnector import  QuikConnector
import logging


class QuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self, quik):
        self.quik = quik

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """

        self._logger.info("Starting quik broker")
        if self.quik.status == QuikConnector.Status.DISCONNECTED:
            self.quik.run()
