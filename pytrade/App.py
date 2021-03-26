import logging
import os
from logging import handlers, config
from threading import Thread
from connector.quik.WebQuikBroker import WebQuikBroker
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.WebQuikFeed import WebQuikFeed
from Strategy import Strategy
from cfg.Config import Config


class App:
    """
    Main application. Build strategy and run.
    """

    def __init__(self):
        # Logger set up
        config = Config
        self._init_logger(config.log_dir)
        self._logger.info("Initializing the App")
        # Quik connector
        self._connector = WebQuikConnector(conn=config.conn, passwd=Config.passwd, account=config.account)

        # Feed2Csv just receive price and level2 for single configured asset and write to data folder
        web_quik_feed = WebQuikFeed(self._connector)
        # self._feed = Feed2Csv(web_quik_feed, config.sec_class, config.sec_code)

        # Broker is not implemented, just a stub.
        web_quik_broker = WebQuikBroker(connector=self._connector, client_code=Config.client_code,
                                        trade_account=Config.trade_account, rabbit_host=config.rabbit_host)

        # Create feed, subscribe events
        # Todo: support making orders
        self._strategy = Strategy(web_quik_feed, web_quik_broker, config.sec_class, config.sec_code)

    def _init_logger(self, logdir):
        # Ensure logging directory exists
        os.makedirs(logdir, exist_ok=True)
        cfgpath = "cfg/logging.cfg"
        logging.config.fileConfig(cfgpath)
        # logging.basicConfig(
        #     level=logging.INFO,
        #     format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        #     datefmt="%Y-%m-%d %H:%M:%S",
        #     handlers=[
        #         #handlers.RotatingFileHandler("log/pytrade.log", maxBytes=(1048576 * 5), backupCount=3),
        #         handlers.RotatingFileHandler(logpath, maxBytes=(1048576 * 5), backupCount=3),
        #         logging.StreamHandler()
        #     ])
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Logging configured from {cfgpath}")

    def main(self):
        """
        Application entry point
        """

        # Start strategy
        Thread(target=self._strategy.run).start()

        # Start connection to web quick server# _rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # # _rabbit_channel = _rabbit_connection.channel()
        # # _rabbit_channel.queue_declare(queue="hello")
        # # _rabbit_channel.basic_publish(exchange="", routing_key="pytrade.broker", body="hello, world!")
        # # _rabbit_channel.close()
        self._connector.run()


if __name__ == "__main__":
    App().main()
