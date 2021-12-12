import logging.config
import os
import sys
import yaml

from broker.Broker import Broker
from strategy.PeriodicalLearnStrategy import *
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.WebQuikFeed import WebQuikFeed
from connector.quik.WebQuikBroker import WebQuikBroker
from connector.CsvFeedConnector import CsvFeedConnector
from connector.EmptyBrokerConnector import EmptyBrokerConnector
from connector.MemoryBrokerConnector import MemoryBrokerConnector
from bunch import bunchify

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
        self._init_logger(config["log.dir"])
        self._logger.info("Initializing the App")

        # Feed and broker
        self._init_connectors(config)
        feed = Feed(self._feed_connector)
        broker = Broker(self._broker_connector)

        if config["app.action"] == "run" and config["interop.is_interop"]:
            self._init_interop(config, feed, broker)
        if config["is_feed2csv"]:
            self._feed2csv = Feed2Csv(feed)

        # Dynamically create the strategy by the name from config
        self._init_strategy(config, feed, broker)
        self._action = config["app.action"]

    def _init_connectors(self, config):
        """
        Dynamically set up feed and broker connectors from config
        """
        self._logger.info("Init broker and feed connectors")
        self._broker_connector = globals()[config["broker.connector"]](config)
        self._feed_connector = globals()[config["feed.connector"]](config)

    def _init_strategy(self, config, feed, broker):
        name = config['strategy']
        self._logger.info(f"Creating strategy {name}")
        self._strategy = globals()[name](feed, broker, config)

    def _init_interop(self, config, feed, broker):
        self._logger.info("Configuring interop mode")
        rabbit_host = config["interop.rabbit.host"]
        self._feed_interop = FeedInterop(feed=feed, rabbit_host=rabbit_host)
        self._broker_interop = BrokerInterop(broker=broker, rabbit_host=rabbit_host)

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

    def run(self):
        """
        Run and trade, maybe using simulators
        """
        self._logger.info("Running")
        self._feed_connector.run()
        self._broker_connector.run()

    def learn(self):
        """
        Learn, not run and trade
        """
        self._logger.info("Learning, not running")
        self._strategy.learn()

    def main(self):
        """
        Application entry point
        """
        getattr(self, self._action)()
        # Start strategy in a separate thread
        # Thread(target=self._strategy.run).start()
        # Run feed and broker connectors
        # self._feed_connector.run()
        # self._broker_connector.run()


if __name__ == "__main__":
    App().main()
