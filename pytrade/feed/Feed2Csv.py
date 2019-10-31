import logging
import datetime as dt
import os
from pytrade.feed.BaseFeed import BaseFeed


class Feed2Csv(BaseFeed):
    """
    Receive ticks and level 2 and persist to csv
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.INFO)

    def __init__(self, feed, sec_class, sec_code, data_dir='./data'):
        super().__init__(feed, sec_class, sec_code)
        # Dump each minute
        self._write_interval = dt.timedelta(minutes=1)
        self._data_dir = data_dir
        self._logger.info("Candles and level2 will be persisted each %s to %s", self._write_interval, self._data_dir)

    def write(self):
        """
        Append collected data to csv. File name contains asset and day. Each day in each file.
        """
        # Get time from first element. Index: (asset, datetime)
        start_time = self.candles.index[0][0]
        file_name = '%s_%s_%s.csv' % (self.sec_class, self.sec_code, start_time.strftime('%Y-%m-%d'))

        # Write then clear candles
        file_path = os.path.join(self._data_dir, file_name)
        self._logger.debug("Writing candles to %s", file_path)
        self.candles.to_csv(file_path, mode='a', header=False)
        self.candles = self.candles.iloc[0:0]

        # Write then clear level2
        start_time = self.level2.index[0][0]
        file_name = '%s_%s_level2_%s.csv' % (self.sec_class, self.sec_code, start_time.strftime('%Y-%m-%d'))
        file_path = os.path.join(self._data_dir, file_name)
        self._logger.debug("Writing level2 to %s", file_path)
        self.level2.to_csv(file_path, mode='a', header=False)
        self.level2 = self.level2.iloc[0:0]

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        # If time interval elapsed, write dataframe to csv
        if (dt.datetime.now() - self._last_heartbeat) > self._write_interval:
            self.write()

        # Store current time as last heart beat
        super().on_heartbeat()
