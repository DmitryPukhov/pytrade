import collections
import logging

import pandas as pd
from pandas import Timedelta


class CsvFeedConnector:
    """
    Reads the data from csv
    """

    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self._logger.info("Init " + __name__)
        candles_path = config["csv_feed_candles"]
        quotes_path = config["csv_feed_quotes"]
        level2_path = config["csv_feed_level2"]
        self._logger.info(f"Candles: {candles_path}, quotes: {quotes_path}, level2:{level2_path}")

        self._subscribers = collections.defaultdict(list)
        # Read the data from csv
        self.candles = pd.read_csv(candles_path, parse_dates=True,
                                   names=['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume'],
                                   index_col=['datetime'])
        self.candles = self.candles[~self.candles.index.duplicated(keep='first')].sort_index()
        self.quotes = pd.read_csv(quotes_path, parse_dates=True, names=['datetime', 'ticker', 'bid', 'ask', 'last'],
                                  index_col=['datetime'])
        self.quotes = self.quotes[~self.quotes.index.duplicated(keep='first')].sort_index()
        self.level2 = pd.read_csv(level2_path, parse_dates=['datetime'],
                                  names=['datetime', 'ticker', 'price', 'bid_vol', 'ask_vol'])
        #self.level2 = self.level2[~self.level2.index.duplicated(keep='first')].sort_index()

    def subscribe_feed(self, asset, subscriber):
        self._subscribers[asset].append(subscriber)

    def run(self):
        ticks = pd.concat([self.quotes.index.to_series(),
                           self.candles.index.to_series(),
                           self.level2['datetime']])
        for dt, tick in ticks.iteritems():
            # Get previous nearest item for this tick
            quote = self.quotes.iloc[self.quotes.index.get_loc(dt)]
            candle = self.candles.iloc[self.candles.index.get_loc(dt)]
            #level2dt= self.level2[self.level2['datetime'] <=dt]['datetime'].max()
            level2 = self.level2[self.level2['datetime']==dt]
            print(quote)
            print(candle)
            print(level2)

    def preprocess(self):
        # Pivot to create feature columns of level2 prices and volumes
        df = self.level2
        df["num"] = df.groupby("datetime").cumcount() + 1
        price_pivoted = df.pivot(index="datetime", columns="num", values="price")
        price_pivoted.columns = "price" + price_pivoted.columns.astype(str)
        price_pivoted["base"] = (price_pivoted["price10"] + price_pivoted["price11"]) / 2
        for n in range(1, len([c for c in price_pivoted.columns if c.startswith("price")]) + 1):
            col = "price" + str(n)
            price_pivoted[col] = price_pivoted[col] - price_pivoted["base"]

        bid_vol_pivoted = df.pivot(index="datetime", columns="num", values="bid_vol")
        bid_vol_pivoted.columns = "bid_vol" + bid_vol_pivoted.columns.astype(str)

        ask_vol_pivoted = df.pivot(index="datetime", columns="num", values="ask_vol")
        ask_vol_pivoted.columns = "as_vol" + ask_vol_pivoted.columns.astype(str)

        pivoted = price_pivoted.join(bid_vol_pivoted).join(ask_vol_pivoted)
        # Form level2

        # Reverse, rolling and reverse back to calc future max and min
        # Add future min/max
        predict_window = "2min"
        self.quotes["nextmax"] = self.quotes["ask"][::-1].rolling(predict_window).max()[::-1]
        self.quotes["nextmin"] = self.quotes["ask"][::-1].rolling(predict_window).min()[::-1]

        # Add last closest
        m = pd.merge_asof(self.quotes, self.candles, left_index=True, right_index=True, tolerance=pd.Timedelta("1 min"))
        print(m.head(10))

# # # Test code todo: remove
# base_dir = "../data/"
# csv_feed = CsvFeedConnector(base_dir + "QJSIM_SBER_candles_2021-11-07.csv",
#                             base_dir + "QJSIM_SBER_quotes_2021-11-07.csv",
#                             base_dir + "QJSIM_SBER_level2_2021-11-07.csv")
# csv_feed.run()
