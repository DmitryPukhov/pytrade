import logging.config
import os
import sys
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
        # Load config respecting the order: defaults, app.yaml, environment vars
        config = self._load_config()

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

    def _load_config(self):
        """
        Load config respecting the order: defaults, app.yaml, environment vars
        """
        # Defaults
        default_cfg_path="cfg/app-defaults.yaml"
        with open("cfg/app-defaults.yaml", "r") as appdefaults:
            config = yaml.safe_load(appdefaults)

        # Custom config, should contain account information
        cfg_path = "cfg/app.yaml"
        if os.path.exists(cfg_path):
            with open(cfg_path) as app:
                config.update(yaml.safe_load(app))
        else:
            sys.exit(f"Config {cfg_path} not found. Please copy cfg/app-defaults.yaml to {cfg_path} and update connection info there.")

        config.update(os.environ)
        return config

    def _init_logger(self, logdir):
        # Ensure logging directory exists
        os.makedirs(logdir, exist_ok=True)
        cfgpaths = ["cfg/log-defaults.cfg", "cfg/log.cfg"]
        for cfgpath in cfgpaths:
            if os.path.exists(cfgpath):
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
