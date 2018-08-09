import logging
import pandas as pd
import datetime as dt
import os


class Feed2Csv:
    """
    Subscribe to ticks, receive them, periodicaly write to csv file
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, sec_class, sec_code, dir='./data'):
        # Dump each minute
        self._write_interval = dt.timedelta(minutes=1)

        self._dir = dir
        self.sec_class = sec_class
        self.sec_code = sec_code

        # Connecting to feed
        self._feed = feed
        self._feed.tick_callbacks.add(self.on_tick)
        self._last_tick_time = dt.datetime.min

        # Price/vol dataframe
        self.data = pd.DataFrame(columns=['price', 'vol'])

    def on_tick(self, class_code, asset_code, tick_time, price, vol):
        """
        New price/vol tick received
        @param class_code exchange SPBFUT for
        :return None
        """
        # Add tick to data
        self.data.loc[pd.to_datetime(tick_time)] = [price, vol]

        # Debugging code
        if (tick_time - self._last_tick_time) >= self._write_interval:
            self.write()
            self._last_tick_time = tick_time

    def write(self):
        """
        Append collected data to csv. File name contains asset and day. Each day in each file.
        """
        file_name = '%s_%s_%s.csv' % (self.sec_class, self.sec_code, self.data.index[0].strftime('%Y-%m-%d'))
        file_path = os.path.join(self._dir, file_name)
        self.data.to_csv(file_path, mode='a', header=True)
