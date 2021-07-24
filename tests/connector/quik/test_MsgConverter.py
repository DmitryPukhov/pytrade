from datetime import datetime
from unittest import TestCase

from connector.quik.MsgConverter import MsgConverter


class TestMsgConverter(TestCase):
    def test_msg2order(self):
        msg = {'msgid': 21001, 'qdate': 20210724, 'qtime': 144005, 'ccode': 'QJSIM', 'scode': 'SBER',
               'sell': 0, 'account': 'NL0011100043', 'price': 29500, 'qty': 1, 'volume': 123, 'balance': 1,
               'yield': 0, 'accr': 0, 'refer': '10815//', 'type': 25, 'firm': 'NC0011100000', 'ucode': '10815',
               'number': '6059372033', 'status': 234, 'price_currency': '', 'settle_currency': ''}
        order = MsgConverter.msg2order(msg)
        self.assertEqual(datetime(2021, 7, 24, 14, 40, 5), order.dt)
        self.assertEqual('QJSIM', order.class_code)
        self.assertEqual('SBER', order.sec_code)
        self.assertEqual('SBER', order.sec_code)
        self.assertFalse(order.is_sell)
        self.assertEqual('NL0011100043', order.account)
        self.assertEqual(29500, order.price)
        self.assertEqual(1, order.quantity)
        self.assertEqual(123, order.volume)
        self.assertEqual(234, order.status)

    def test_decode_datetime(self):
        dt = MsgConverter().decode_datetime(20210724, 160412)
        self.assertEqual(2021, dt.year)
        self.assertEqual(7, dt.month)
        self.assertEqual(24, dt.day)
        self.assertEqual(16, dt.hour)
        self.assertEqual(4, dt.minute)
        self.assertEqual(12, dt.second)
