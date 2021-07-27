import datetime
import logging
import datetime as dt
import os
from collections import defaultdict

import pandas as pd
from pandas import DataFrame
from feed.Feed import Feed
from model.feed.Asset import Asset


class Feed2Csv:
    """
    Receive ticks and level 2 and persist to csv
    """
    def __init__(self, feed: Feed,  data_dir: str = './data'):
        self._logger = logging.getLogger(__name__)
        self._feed = feed
        self._feed.subscribe_feed(Asset("*","*"), self)

        # Dump periodically
        self._write_interval = dt.timedelta(seconds=30)
        self._data_dir = data_dir
        self._logger.info("Candles and level2 will be persisted each %s to %s", self._write_interval, self._data_dir)
        self._last_write_time = dt.datetime.min
        self._last_processed_times = defaultdict(lambda: pd.Timestamp.min)
        self.is_writing = False

    def write(self, df, tag):
        """
        Group dataframe by ticker and day. Write each group to separate file
        :param df: dataframe to group and write
        :param tag: text tag, will be appended to file name
        """
        if self.is_writing:
            self._logger.debug(f"Previous {tag} writing is still in progress, exiting.")
            return
        try:
            self.is_writing = True
            self._logger.debug(f"Writing {tag} to csv")

            # Get the data, not saved previously
            last_processed_time = self._last_processed_times[tag]
            df = df[df.index.get_level_values(0) > last_processed_time]

            # Append to csv if new data exists
            if not df.empty:
                df.groupby([df.index.get_level_values(0).dayofyear, df.index.get_level_values(1)]).apply(
                    lambda df_daily: self._write_ticker_by_day(df_daily, tag))
                self._last_processed_times[tag] = df.index.get_level_values(0).max()
            else:
                self._logger.debug(f"{tag} is empty, nothing to write")
        except Exception as ex:
            self._logger.error(ex)
        finally:
            self.is_writing = False

    def _write_ticker_by_day(self, df: DataFrame, data_type):
        """
        Compose file name from ticker and
        :param df: Dataframe, all rows have the same day and ticker in index
        :param data_type: tag to use in file name
        """
        # Form file name
        date = df.first_valid_index()[0].date()
        ticker = df.first_valid_index()[1].replace('/','_')
        df.first_valid_index()[1].replace('/', '_')
        file_name = '%s_%s_%s.csv' % (ticker, data_type, date.strftime('%Y-%m-%d'))
        file_path = os.path.join(self._data_dir, file_name)
        self._logger.debug("Writing %s to %s", data_type, os.path.abspath(file_path))
        # Write to file
        df.to_csv(file_path, mode='a', header=False)

    def on_heartbeat(self):
        """
        Heartbeat received
        """
        self._logger.debug("Got heartbeat")
        # If time interval elapsed, write dataframe to csv
        if (dt.datetime.now() - self._last_write_time) < self._write_interval:
            return
        self._logger.debug("Writing to csv")
        self._last_write_time = dt.datetime.now()
        self.write(self._feed.level2, 'level2')
        self.write(self._feed.candles, 'candles')
        self.write(self._feed.quotes, 'quotes')
        self._last_write_time = dt.datetime.now()
