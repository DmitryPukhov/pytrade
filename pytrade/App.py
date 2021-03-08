import logging
from threading import Thread

from connector.quik.WebQuikBroker import WebQuikBroker
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.WebQuikFeed import WebQuikFeed
from pytrade.feed.Feed2Csv import Feed2Csv
from pytrade.Strategy import Strategy
from pytrade.Config import Config


class App:
    """
    Main application. Build strategy and run.
    """
    # _logger = logging.getLogger(__name__)
    # _logger.setLevel(logging.INFO)

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.INFO)
        self._logger.info("Initializing the App")
        config = Config

        # Quik connector
        self._connector = WebQuikConnector(conn=config.conn, passwd=Config.passwd, account=config.account)

        # Feed2Csv just receive price and level2 for single configured asset and write to data folder
        web_quik_feed = WebQuikFeed(self._connector)
        #self._feed = Feed2Csv(web_quik_feed, config.sec_class, config.sec_code)

        # Broker is not implemented, just a stub.
        web_quik_broker = WebQuikBroker(connector=self._connector, client_code=Config.client_code, trade_account=Config.trade_account)

        # Create feed, subscribe events
        # Todo: support making orders
        self._strategy = Strategy(web_quik_feed, web_quik_broker, config.sec_class, config.sec_code)

    def main(self):
        """
        Application entry point
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                # handlers.RotatingFileHandler("pytrade.log", maxBytes=(1048576 * 5), backupCount=3),
                logging.StreamHandler()
            ])

        # Start strategy
        Thread(target=self._strategy.run).start()

        # Start connection to web quick server
        self._connector.run()


if __name__ == "__main__":
    App().main()
