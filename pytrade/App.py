import logging

from pytrade.connector.quik.QuikConnector import QuikConnector
from pytrade.connector.quik.QuikBroker import QuikBroker
from pytrade.connector.quik.QuikFeed import QuikFeed
from pytrade.Strategy import Strategy


class App:
    """
    Main application. Build strategy and run.
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self):
        self._logger.info("Initializing the App")
        quik = QuikConnector(host="192.168.1.104", port=1111, passwd='1', account='SPBFUT00998')

        # Create feed, subscribe events
        self._broker = QuikBroker(quik)
        self._feed = QuikFeed(quik, 'SPBFUT', 'RIU8')
        self._strategy = Strategy(self._feed, self._broker)
        # self._feed.tick_callbacks.add(self.on_tick)
        # self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        # self._heart_beating = False

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
