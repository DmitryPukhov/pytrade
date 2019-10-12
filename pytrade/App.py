import logging
from logging import handlers

from pytrade.Strategy import Strategy
from pytrade.connector.quik.QuikFeed import QuikFeed
from pytrade.Config import Config
from pytrade.connector.quik.WebQuikConnector import WebQuikConnector


class App:
    """
    Main application. Build strategy and run.
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self):
        self._logger.info("Initializing the App")
        config = Config
        quik = WebQuikConnector(conn=config.conn, passwd=Config.passwd, account=config.account)

        # Create feed, subscribe events
        self._feed = QuikFeed(quik, config.sec_class, config.sec_code)
        # Todo: support making orders
        # self._broker = QuikBroker(quik)
        self._broker = None
        #self._strategy = Strategy(self._feed, self._broker, config.sec_class, config.sec_code)
        self._strategy = Strategy(self._feed, self._broker, config.sec_class, config.sec_code)
        # feed2csv = Feed2Csv(self._feed, config.sec_class, config.sec_code)

    def main(self):
        """
        Application entry point
        :return: None
        """
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                #handlers.RotatingFileHandler("pytrade.log", maxBytes=(1048576 * 5), backupCount=3),
                logging.StreamHandler()
            ])
        self._feed.start()
        # Todo: support making orders
        # self._broker.start()


if __name__ == "__main__":
    App().main()
