from datetime import datetime

from model.broker.Order import Order


class MsgConverter:
    @staticmethod
    def decode_datetime(date: int, time: int) -> datetime:
        """
        Decode time like date=20210724, time=144005
        """
        year = date // 10000
        month = (date % 10000) // 100
        day = date % 100
        hour = time // 10000
        minute = (time % 10000) // 100
        sec = time % 100
        return datetime(year, month, day, hour, minute, sec)

    @staticmethod
    def msg2order(msg) -> Order:
        """
        Convert Quik message to Order model
        """
        # msg={'msgid': 21001, 'qdate': 20210724, 'qtime': 144005, 'ccode': 'QJSIM', 'scode': 'SBER',
        # 'sell': 0, 'account': 'NL0011100043', 'price': 29500, 'qty': 1, 'volume': 295000, 'balance': 1,
        # 'yield': 0, 'accr': 0, 'refer': '10815//', 'type': 25, 'firm': 'NC0011100000', 'ucode': '10815',
        # 'number': '6059372033', 'status': 1, 'price_currency': '', 'settle_currency': ''}
        return Order(number=msg['number'],
                     dt=MsgConverter.decode_datetime(msg['qdate'],msg['qtime']),
                     class_code=msg['ccode'],
                     sec_code=msg['scode'],
                     is_sell=msg['sell'],
                     account=msg['account'],
                     price=msg['price'],
                     quantity=msg['qty'],
                     volume=msg['volume'],
                     status=msg['status'])
