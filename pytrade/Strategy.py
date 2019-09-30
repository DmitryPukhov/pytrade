import logging
#import talib as ta
import pandas as pd
import datetime as dt


class Strategy:
    """
    Strategy receives data from feed and make orders to broker
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, broker, sec_class, sec_code):
        self._feed = feed
        self.sec_class = sec_class
        self.sec_code = sec_code

        # Connecting to broker
        self._broker = broker

        # Connecting to feed
        self._feed.tick_callbacks.add(self.on_tick)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False
        self._flag = False
        self._last_tick_time = dt.datetime.min

        # Main data with price etc.
        self.data = pd.DataFrame(columns=['price', 'vol'])

    def on_tick(self, class_code, asset_code, tick_time, price, vol):
        """
        New price/vol tick received
        """
        # Add tick to data
        self.data.loc[pd.to_datetime(tick_time)] = [price, vol]
        self._logger.debug("Received tick: time=%s, asset=%s\\%s, price=%s, vol=%s", tick_time, class_code, asset_code, price, vol)
        # Debugging code
        # if (tick_time - self._last_tick_time).seconds > 10:
        #     print("last ticks:")
        #     print(self.data.tail())
        self._last_tick_time = tick_time

        # Debugging code
        # if not self._flag and self.sec_code == 'RIU8':
        # self._broker.buy(class_code='SPBFUT', sec_code='RIU8', price=price + 50, quantity=1)
        # self._broker.sell(class_code=self.sec_class, sec_code=self.sec_code, price=price-100, quantity=1)
        # self._flag = True

    def on_heartbeat(self):
        """
        Heartbeat received
        :return: None
        """
