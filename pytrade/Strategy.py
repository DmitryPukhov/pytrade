# import talib as ta
import pandas as pd
from pytrade.feed.BaseFeed import BaseFeed
pd.options.display.width = 0


class Strategy(BaseFeed):

    def __init__(self, feed, broker, sec_class, sec_code):
        super().__init__(feed, sec_class, sec_code)
        self._broker = broker

    def on_heartbeat(self):
        """
        Heartbeat received
        :return: None
        """
        super().on_heartbeat()
        self._logger.debug("Strategy heart beat")
