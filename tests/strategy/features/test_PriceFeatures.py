from datetime import datetime
from unittest import TestCase

import numpy as np
import pandas as pd
from pytrade.strategy.features.PriceFeatures import PriceFeatures


class TestPriceFeatures(TestCase):

    def test_price_features__(self):
        # quotes columns: ['datetime', 'ticker', 'bid', 'ask', 'last', 'last_change']
        quotes = pd.DataFrame([
            # 7:00-7:05
            {'datetime': datetime.fromisoformat('2021-12-08 07:00:01'), 'ticker': 'asset1', 'bid': 1,
             'ask': 11, 'last': 110},
            {'datetime': datetime.fromisoformat('2021-12-08 07:00:10'), 'ticker': 'asset1', 'bid': 1,
             'ask': 11, 'last': 110},
            {'datetime': datetime.fromisoformat('2021-12-08 07:01:00'), 'ticker': 'asset1', 'bid': 2,
             'ask': 22, 'last': 20},
            # 7:05-7:10
            {'datetime': datetime.fromisoformat('2021-12-08 07:01:59'), 'ticker': 'asset1', 'bid': 3,
             'ask': 33, 'last': 30},
            {'datetime': datetime.fromisoformat('2021-12-08 07:02:05'), 'ticker': 'asset1', 'bid': 2,
             'ask': 22, 'last': 20},
            {'datetime': datetime.fromisoformat('2021-12-08 07:03:00'), 'ticker': 'asset1', 'bid': 1,
             'ask': 11, 'last': 110},
        ]).set_index(['datetime', 'ticker'])

        # Call
        features = PriceFeatures().minmax_past(quotes, 1, 'min', 3)

        # Assert
        # Aggregated -1 minute min/max
        self.assertEqual([11.0, 11.0, 22.0, 33.0, 33.0, 22.0], features['-1*1min_high'].values.tolist())
        self.assertEqual([1.0, 1.0, 1.0, 2.0, 2.0, 1.0], features['-1*1min_low'].values.tolist())
        # Aggregated -2
        self.assertEqual([11.0, 11.0, 11.0, 22.0, 22.0, 33.0], features['-2*1min_high'].values.tolist())
        self.assertEqual([1.0, 1.0, 1.0, 1.0, 1.0, 2.0], features['-2*1min_low'].values.tolist())
        # Aggregated -3
        self.assertEqual([-1, -1, -1, 11.0, 11.0, 22.0], features['-3*1min_high'].fillna(-1).tolist())
        self.assertEqual([-1, -1, -1, 1, 1, 1], features['-3*1min_low'].fillna(-1).tolist())
