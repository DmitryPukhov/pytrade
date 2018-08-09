import logging

from pytrade.connector.quik.QuikConnector import QuikConnector
from pytrade.connector.quik.QuikBroker import QuikBroker
from pytrade.connector.quik.QuikFeed import QuikFeed
from pytrade.Feed2Csv import Feed2Csv
from pytrade.Strategy import Strategy
from pytrade.Config import Config


class App:
    """
    Main application. Build strategy and run.
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self):
        self._logger.info("Initializing the App")
        config = Config
        quik = QuikConnector(host=config.host, port=config.port, passwd=Config.passwd, account=config.account)

        # Create feed, subscribe events
        self._broker = QuikBroker(quik)
        self._feed = QuikFeed(quik, config.sec_class, config.sec_code)
        self._strategy = Strategy(self._feed, self._broker, config.sec_class, config.sec_code)
        #feed2csv = Feed2Csv(self._feed, config.sec_class, config.sec_code)

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
