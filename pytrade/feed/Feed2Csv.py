import logging
import datetime as dt
import os
from pandas import DataFrame
from feed.BaseFeed import BaseFeed


class Feed2Csv(BaseFeed):
    """
    Receive ticks and level 2 and persist to csv
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, sec_class, sec_code, data_dir='./data'):
        super().__init__(feed, sec_class, sec_code)

        # Dump periodically
        self._write_interval = dt.timedelta(seconds=10)
        self._data_dir = data_dir
        self._logger.info("Candles and level2 will be persisted each %s to %s", self._write_interval, self._data_dir)
        self._last_write_time = dt.datetime.min

    def write(self, df, data_type):
        """
        Group dataframe by ticker and day. Write each group to separate file
        :param df: dataframe to group and write
        :param data_type: text tag, will be appended to file name
        """
        if not df.empty:
            df.groupby([df.index.get_level_values(0).dayofyear, df.index.get_level_values(1)]).apply(
                lambda df_daily: self._write_ticker_by_day(df_daily, data_type))

    def _write_ticker_by_day(self, df: DataFrame, data_type):
        """
        Compose file name from ticker and
        :param df: Dataframe, all rows have the same day and ticker in index
        :param data_type: tag to use in file name
        """
        # Form file name
        date = df.first_valid_index()[0].date()
        ticker = df.first_valid_index()[1].replace('/', '_')
        file_name = '%s_%s_%s.csv' % (ticker, data_type, date.strftime('%Y-%m-%d'))
        file_path = os.path.join(self._data_dir, file_name)
        self._logger.debug("Writing %s to %s", data_type, os.path.abspath(file_path))
        # Write to file
        df.to_csv(file_path, mode='a', header=False)

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        # If time interval elapsed, write dataframe to csv
        if (dt.datetime.now() - self._last_write_time) > self._write_interval:
            self.write(self.candles, 'candles')
            self.write(self.level2, 'level2')

            self._last_write_time = dt.datetime.now()

        # Store current time as last heart beat
        super().on_heartbeat()
