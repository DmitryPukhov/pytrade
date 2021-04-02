import logging.config
import os
from threading import Thread
import yaml

from connector.quik.WebQuikBroker import WebQuikBroker
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.WebQuikFeed import WebQuikFeed
from Strategy import Strategy


# from cfg.Config import Config


class App:
    """
    Main application. Build strategy and run.
    """

    def __init__(self):
        # Config set up. Environment overrides app.yaml
        with open("cfg/app.yaml", "r") as f:
            config = yaml.safe_load(f)
            config.update(os.environ)

        # Logger set up
        self._init_logger(config["log_dir"])
        self._logger.info("Initializing the App")

        # Quik connector
        self._connector = WebQuikConnector(conn=config["conn"], passwd=config["passwd"], account=config["account"])

        # Feed2Csv just receive price and level2 for single configured asset and write to data folder
        web_quik_feed = WebQuikFeed(self._connector, rabbit_host=config["rabbit_host"])
        # self._feed = Feed2Csv(web_quik_feed, config.sec_class, config.sec_code)

        # Broker is not implemented, just a stub.
        web_quik_broker = WebQuikBroker(connector=self._connector, client_code=config["client_code"],
                                        trade_account=config["trade_account"], rabbit_host=config["rabbit_host"])

        # Create feed, subscribe events
        # Todo: support making orders
        self._strategy = Strategy(web_quik_feed, web_quik_broker, config["sec_class"], config["sec_code"])

    def _init_logger(self, logdir):
        # Ensure logging directory exists
        os.makedirs(logdir, exist_ok=True)
        cfgpath = "cfg/logging.cfg"
        logging.config.fileConfig(cfgpath)
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Logging configured from {cfgpath}")

    def main(self):
        """
        Application entry point
        """
        # Start strategy
        Thread(target=self._strategy.run).start()
        self._connector.run()


if __name__ == "__main__":
    App().main()
