import logging

from pytrade.connector.quik.QuikConnector import QuikConnector
from pytrade.connector.quik.QuikBroker import QuikBroker
from pytrade.connector.quik.QuikFeed import QuikFeed


class App:
    """
    Main application. Build strategy and run.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self):
        self._logger.info("Initializing the App")
        quik = QuikConnector()
        self._broker = QuikBroker(quik)
        self._feed = QuikFeed(quik)

    def main(self):
        """
        Application entry point
        :return: None
        """
        self._feed.start()
        self._broker.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    App().main()
