from datetime import datetime
from unittest import TestCase

from pytrade.connector.quik.WebQuikFeed import WebQuikFeed
from pytrade.model.feed.Asset import Asset


class TestWebQuikFeed(TestCase):
    def test_level2_of(self):
        # Sample of level2. {'msgid': 21014, 'quotes': {'QJSIM¦SBER': {'lines': {'22806':
        # {'b': 234, 's': 0, 'by': 0, 'sy': 0}, '22841': {'b': 437, 's': 0, 'by': 0, 'sy': 0},
        # '22853': {'b': 60, 's': 0, 'by': 0, 'sy': 0}, '22878': {'b': 82, 's': 0, 'by': 0, 'sy': 0},
        # '22886': {'b': 138, 's': 0, 'by': 0, 'sy': 0}, '22895': {'b': 1, 's': 0, 'by': 0, 'sy': 0},...
        data = {1: {'b': 4, 's': 7, 'by': 0, 'sy': 0},
                2: {'b': 5, 's': 8, 'by': 0, 'sy': 0},
                3: {'b': 6, 's': 9, 'by': 0, 'sy': 0}}
        level2 = WebQuikFeed._level2_of(datetime(2021, 7, 23, 12, 51), Asset("code1", "sec1"), data)
        self.assertEqual(level2.dt, datetime(2021, 7, 23, 12, 51))
        self.assertEqual(level2.asset, Asset("code1", "sec1"))
        self.assertEqual([1, 2, 3], [item.price for item in level2.items])
        self.assertEqual([4, 5, 6], [item.bid_vol for item in level2.items])
        self.assertEqual([7, 8, 9], [item.ask_vol for item in level2.items])

    def test_quote_of_empty(self):
        data = {}
        quote = WebQuikFeed._quote_of(None, data)
        self.assertIsNotNone(quote.dt)
        self.assertIsNone(quote.bid)
        self.assertIsNone(quote.ask)
        self.assertIsNone(quote.last)
        self.assertIsNone(quote.last_change)

    def test_quote_of(self):
        data = {"bid": 1, "offer": 2, "last": 3, "lastchange": 4}
        quote = WebQuikFeed._quote_of("stock1¦asset1", data)
        self.assertIsNotNone(quote.dt)
        self.assertEqual(Asset("stock1", "asset1"), quote.asset)
        self.assertEqual(1, quote.bid)
        self.assertEqual(2, quote.ask)
        self.assertEqual(3, quote.last)
        self.assertEqual(4, quote.last_change)

    def test_ohlcv_of(self):
        data = {"d": "2019-10-01 10:02:00", "o": 1, "c": 2, "h": 3, "l": 4, "v": 5}
        ohlcv = WebQuikFeed._ohlcv_of("stock1¦asset1", data)
        self.assertEqual(ohlcv.asset, Asset("stock1","asset1"))
        self.assertEqual(ohlcv.dt, datetime(2019, 10, 1, 10, 2, 0))
        self.assertEqual(ohlcv.o, 1)
        self.assertEqual(ohlcv.h, 3)
        self.assertEqual(ohlcv.l, 4)
        self.assertEqual(ohlcv.c, 2)
        self.assertEqual(ohlcv.v, 5)

    def test_ticker_of_full_asset(self):
        ticker = WebQuikFeed._ticker_of(Asset("class1", "sec1"))
        self.assertEqual("class1|sec1", ticker)

    def test_ticker_of_None(self):
        ticker = WebQuikFeed._ticker_of(Asset(None, None))
        self.assertEqual("None|None", ticker)

    def test_ticker_of_empty(self):
        ticker = WebQuikFeed._ticker_of(Asset("", ""))
        self.assertEqual("|", ticker)

    def test_asset_of_empty(self):
        asset = WebQuikFeed._asset_of("")
        self.assertIsNone(asset)

    def test_asset_of_none(self):
        asset = WebQuikFeed._asset_of(None)
        self.assertIsNone(asset)

    def test_asset_of_3partsname(self):
        asset: Asset = WebQuikFeed._asset_of("QJSIM¦SBER¦0")
        self.assertEqual("QJSIM", asset.class_code)
        self.assertEqual("SBER", asset.sec_code)

    def test_asset_of_2partsname(self):
        asset: Asset = WebQuikFeed._asset_of("c1ode1¦a1sset1")
        self.assertEqual("c1ode1", asset.class_code)
        self.assertEqual("a1sset1", asset.sec_code)

    def test_asset_of_onlyname(self):
        asset: Asset = WebQuikFeed._asset_of("a1sset1")
        self.assertIsNone(asset.class_code)
        self.assertEqual("a1sset1", asset.sec_code)
