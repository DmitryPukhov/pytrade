from datetime import datetime
from unittest import TestCase

import pandas as pd

from pytrade.strategy.features.TargetFeatures import TargetFeatures


class TestTargetFeatures(TestCase):

    def test_target_features__window_should_include_current(self):
        # quotes columns: ['datetime', 'ticker', 'bid', 'ask', 'last', 'last_change']
        quotes = pd.DataFrame([{'datetime': datetime.fromisoformat('2021-12-08 07:00:00'), 'ticker': 'asset1', 'bid': 1,
                                'ask': 10, 'last': 5},
                               {'datetime': datetime.fromisoformat('2021-12-08 07:01:01'), 'ticker': 'asset1', 'bid': 4,
                                'ask': 6, 'last': 5}
                               ]).set_index('datetime')

        withminmax = TargetFeatures().with_min_max_future(quotes, 1, 'min')
        self.assertEqual([1, 4], withminmax['fut_bid_min'].values.tolist())
        self.assertEqual([10, 6], withminmax['fut_ask_max'].values.tolist())

    def test_target_features__window_should_include_right_bound(self):
        # quotes columns: ['datetime', 'ticker', 'bid', 'ask', 'last', 'last_change']
        quotes = pd.DataFrame([{'datetime': datetime.fromisoformat('2021-12-08 07:00:00'), 'ticker': 'asset1', 'bid': 4,
                                'ask': 6, 'last': 5},
                               {'datetime': datetime.fromisoformat('2021-12-08 07:00:59'), 'ticker': 'asset1', 'bid': 1,
                                'ask': 10, 'last': 5}
                               ]).set_index('datetime')

        withminmax = TargetFeatures().with_min_max_future(quotes, 1, 'min')
        self.assertEqual([1, 1], withminmax['fut_bid_min'].values.tolist())
        self.assertEqual([10, 10], withminmax['fut_ask_max'].values.tolist())

    def test_target_features__(self):
        # quotes columns: ['datetime', 'ticker', 'bid', 'ask', 'last', 'last_change']
        quotes = pd.DataFrame([
            {'datetime': datetime.fromisoformat('2021-11-26 17:00:00'), 'ticker': 'asset1', 'bid': 4, 'ask': 6},
            {'datetime': datetime.fromisoformat('2021-11-26 17:00:30'), 'ticker': 'asset1', 'bid': 1, 'ask': 10},
            {'datetime': datetime.fromisoformat('2021-11-26 17:00:59'), 'ticker': 'asset1', 'bid': 3, 'ask': 7},
            {'datetime': datetime.fromisoformat('2021-11-26 17:01:58'), 'ticker': 'asset1', 'bid': 2, 'ask': 8},

            {'datetime': datetime.fromisoformat('2021-11-26 17:03:00'), 'ticker': 'asset1', 'bid': 4, 'ask': 6},
            {'datetime': datetime.fromisoformat('2021-11-26 17:04:00'), 'ticker': 'asset1', 'bid': 3, 'ask': 7},
            {'datetime': datetime.fromisoformat('2021-11-26 17:05:00'), 'ticker': 'asset1', 'bid': 4, 'ask': 6},
            {'datetime': datetime.fromisoformat('2021-11-26 17:06:00'), 'ticker': 'asset1', 'bid': 3, 'ask': 7}
        ]).set_index('datetime')

        withminmax = TargetFeatures().with_min_max_future(quotes, 1, 'min')

        self.assertEqual([1, 1, 2, 2, 4, 3, 4, 3], withminmax['fut_bid_min'].values.tolist())
        self.assertEqual([10, 10, 8, 8, 6, 7, 6, 7], withminmax['fut_ask_max'].values.tolist())
