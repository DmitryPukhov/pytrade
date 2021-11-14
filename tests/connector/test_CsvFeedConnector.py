from unittest import TestCase

import pandas as pd

from pytrade.connector.CsvFeedConnector import CsvFeedConnector
from datetime import datetime

from model.feed.Asset import Asset


class TestCsvFeedConnector(TestCase):
    def test_level2_of(self):
        # Set input
        dt = datetime.fromisoformat("2021-11-14 10:00")
        data = {'datetime': [dt, dt],
                'ticker': ['stock1/ticker1', 'stock1/ticker1'],
                'price': [1, 11],
                'bid_vol': [2, 22],
                'ask_vol': [3, 33]}
        data = pd.DataFrame(data).to_numpy()

        # Process
        level2 = CsvFeedConnector._level2_of(data)

        # Assert
        self.assertEqual(level2.asset, Asset("stock1", "ticker1"))
        self.assertEqual(level2.dt, dt)
        self.assertEqual([item.price for item in level2.items], [1, 11])
        self.assertEqual([item.bid_vol for item in level2.items], [2, 22])
        self.assertEqual([item.ask_vol for item in level2.items], [3, 33])

    def test__quote_of(self):
        # Set input
        dt = datetime.now()
        data = {'ticker': str(Asset("stock1", "name1")), 'bid': 1, 'ask': 2, 'last': 3, 'last_change': 4}
        # Call
        quote = CsvFeedConnector._quote_of(dt, data)
        # Assert
        self.assertEqual(quote.dt, dt)
        self.assertEqual(quote.asset, Asset.of(data['ticker']))
        self.assertEqual(quote.bid, data['bid'])
        self.assertEqual(quote.ask, data['ask'])
        self.assertEqual(quote.last, data['last'])
        self.assertEqual(quote.last_change, data['last_change'])

    def test__ohlcv_of(self):
        # Set input
        dt = datetime.now()
        data = {'ticker': str(Asset("stock1", "name1")), 'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5}
        # Call
        candle = CsvFeedConnector._ohlcv_of(dt, data)
        # Assert
        self.assertEqual(candle.dt, dt)
        self.assertEqual(candle.asset, Asset.of(data['ticker']))
        self.assertEqual(candle.o, data['open'])
        self.assertEqual(candle.h, data['high'])
        self.assertEqual(candle.l, data['low'])
        self.assertEqual(candle.c, data['close'])
        self.assertEqual(candle.v, data['volume'])
