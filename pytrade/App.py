import logging

from pytrade.connector.quik.QuikConnector import QuikConnector
from pytrade.connector.quik.QuikBroker import QuikBroker
from pytrade.connector.quik.QuikFeed import QuikFeed


class App:
    """
    Main application. Build strategy and run.
    """

    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self):
        self._logger.info("Initializing the App")
        quik = QuikConnector(host="192.168.1.104", port=1111, passwd='1', account='SPBFUT00998')
        self._broker = QuikBroker(quik)

        # Create feed, subscribe events
        self._feed = QuikFeed(quik, 'SPBFUT', 'RIU8')
        self._feed.tick_callbacks.add(self.on_tick)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False

    def main(self):
        """
        Application entry point
        :return: None
        """
        self._feed.start()
        self._broker.start()

    def on_tick(self, class_code, sec_code, price, vol):
        """Tick callback"""
        self._logger.info('We received a great tick! sec_code: %s, price: %s, vol:%s' % (sec_code, price, vol))

    def on_heartbeat(self):
        """
        Any service, checks when system is heartbeating
        :return: None
        """
        if not self._heart_beating:
            # Action during first heartbeat
            self._broker.kill_all_orders()

        self._heart_beating=True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    App().main()
