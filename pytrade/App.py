import logging.config
import os
import sys
import yaml

from strategy.Strategy1 import *
from connector.quik.WebQuikBroker import WebQuikBroker
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.WebQuikFeed import WebQuikFeed
from feed.Feed import Feed
from feed.Feed2Csv import Feed2Csv
from interop.BrokerInterop import BrokerInterop
from interop.FeedInterop import FeedInterop


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

        # Quik connector, single instance used by all brokers and feeds
        self._connector = WebQuikConnector(conn=config["conn"], passwd=config["passwd"], account=config["account"])
        # Adapters for broker and feed
        feed_adapter = WebQuikFeed(self._connector)
        broker_adapter = WebQuikBroker(connector=self._connector, client_code=config["client_code"],
                                       trade_account=config["trade_account"])
        # Feed
        feed = Feed(feed_adapter, config["sec_class"], config["sec_code"])

        if config["is_interop"]:
            self._init_interop(config, feed, broker_adapter)
        if config["is_feed2csv"]:
            self._feed2csv = Feed2Csv(feed, config["sec_class"], config["sec_code"])

        # Dynamically create the strategy by the name from config
        self._init_strategy(config,feed, broker_adapter)

    def _init_strategy(self, config, feed, broker):
        name = config['strategy']
        self._logger.info(f"Creating strategy {name}")
        self._strategy = globals()[name](feed, broker, config)

    def _init_interop(self, config, feed, broker_adapter):
        self._logger.info("Configuring interop mode")
        rabbit_host = config["rabbit_host"]
        self._feed_interop = FeedInterop(feed=feed, rabbit_host=rabbit_host)
        self._broker_interop = BrokerInterop(broker_adapter=broker_adapter, rabbit_host=rabbit_host)

    def _load_config(self):
        """
        Load config respecting the order: defaults, app.yaml, environment vars
        """
        # Defaults
        default_cfg_path = "cfg/app-defaults.yaml"
        with open(default_cfg_path, "r") as appdefaults:
            config = yaml.safe_load(appdefaults)

        # Custom config, should contain account information
        cfg_path = "cfg/app.yaml"
        if os.path.exists(cfg_path):
            with open(cfg_path) as app:
                config.update(yaml.safe_load(app))
        else:
            sys.exit(
                f"Config {cfg_path} not found. Please copy cfg/app-defaults.yaml to {cfg_path} "
                f"and update connection info there.")

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

        # Start strategy in a separate thread
        # Thread(target=self._strategy.run).start()
        # Run connector in current thread. This single connector instance is used across the whole app
        self._connector.run()


if __name__ == "__main__":
    App().main()
