# import talib as ta
import _thread
import json
import logging
import sys
from threading import Thread

import pandas as pd
from feed.BaseFeed import BaseFeed
pd.options.display.width = 0


class Strategy:

    def __init__(self, feed, broker, sec_class, sec_code):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._broker = broker
        self._sec_class = sec_class
        self._sec_code = sec_code

    def run(self):
        # Subscribe to receive feed for the asset
        self._feed.subscribe_feed(self._sec_class, self._sec_code, self)
        # For debugging read command from console
        # op = ""
        # while op != "q":
        #     op = input("Enter q for quit, b for buy or s for sell:")
        #     if op.lower() == "b":
        #         self._broker.buy(self._sec_class, self._sec_code, 340, 1)
        #     elif op.lower() == "s":
        #         self._broker.sell(self._sec_class, self._sec_code, 210, 1)
        #     elif op.lower() == "q":
        #         break
        # # Interrupt webquik socket thread and exit
        # print("Exit")
        # _thread.interrupt_main()

    def on_candle(asset_class, asset_code, dt, o, h, l_, c, v):
        ...


