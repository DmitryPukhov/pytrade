import logging

from connector.quik.WebQuikBroker import WebQuikBroker
from model.broker.Order import Order


class Broker:
    """
    Broker holds account info and can  make orders.
    Supports only simple buy/sell at the moment
    Todo: add different types of orders: stop, market ...
    """

    def __init__(self, broker_connector: WebQuikBroker):
        self._logger = logging.getLogger(__name__)
        self._broker_connector = broker_connector
        self.client_code = self._broker_connector.client_code
        self.trade_account = self._broker_connector.trade_account
        self._broker_connector = broker_connector
        self._broker_connector.subscribe_broker(self)
        self._logger.info("Initialized")
        self._subscribers = set()

        # Domain entities
        self.orders = set()

    def on_order_answer(self, msg):
        self._logger.info(f"Got msg: {msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_order_answer', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_order_answer(msg)

    def buy(self, class_code, sec_code, price, quantity):
        self._logger.info(f"Got buy command. class_code:{class_code}, sec_code: {sec_code}, "
                          f"price: {price}, quantity: {quantity}")
        self._broker_connector.buy(class_code, sec_code, price, quantity)

    def send_raw_msg(self, msg):
        """
        Send raw message to broker, useful for debugging.
        """
        self._logger.info(f"Sending raw message to broker: {msg}")
        self._broker_connector.send_raw_msg(msg)

    def sell(self, class_code, sec_code, price, quantity):
        self._logger.info(f"Got sell command. class_code:{class_code}, sec_code: {sec_code}, "
                          f"price: {price}, quantity: {quantity}")
        self._broker_connector.sell(class_code, sec_code, price, quantity)

    def on_trades_fx(self, msg):
        self._logger.debug(f"On trades fx. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_trades_fx', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_trades_fx(msg)

    def on_trade_accounts(self, msg):
        # Information about my account. Usually one for stocks, one for futures.
        # {"msgid":21022,"trdacc":"NL0011100043","firmid":"NC0011100000","classList":["QJSIM"],"mainMarginClasses":["QJSIM"],"limitsInLots":0,"limitKinds":["0","1","2"]}
        self._logger.debug(f"On trade accounts. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_trade_accounts', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_trade_accounts(msg)

    def on_orders(self, order: Order):
        # Information about my orders
        # msg={'msgid': 21001, 'qdate': 20210416, 'qtime': 195529, 'ccode': 'QJSIM',
        # 'scode': 'SBER', 'sell': 0, 'account': 'NL0011100043', 'price': 28250, 'qty': 1, 'volume': 282500,
        # 'balance': 0, 'yield': 0, 'accr': 0, 'refer': '10058//', 'type': 24, 'firm': 'NC0011100000',
        # 'ucode': '10058', 'number': '5830057748', 'status': 2, 'price_currency': '', 'settle_currency': ''}
        self._logger.debug(f"On orders. order={order}")
        self.orders.add(order)
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_orders', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_orders(order)

    def on_trades(self, msg):
        self._logger.debug(f"On trades. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_trades', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_trades(msg)

    def on_money_limits(self, msg):
        self._logger.debug(f"On money limits. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_money_limits', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_money_limits(msg)

    def on_limits(self, msg):
        self._logger.debug(f"On limits. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_limits', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_limits(msg)

    def on_stock_limits(self, msg):
        self._logger.debug(f"On stock limits. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_stock_limits', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_stock_limits(msg)

    def on_limit_received(self, msg):
        self._logger.debug(f"Limit has received. msg={msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_limit_received', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_limit_received(msg)

    def subscribe_broker(self, subscriber):
        """
        Subscribe to broker events - trades, account etc.
        :param subscriber broker class, inherited from broker'
        """
        # Register given feed callback
        self._subscribers.add(subscriber)

    def on_reply(self, msg: str):
        """
        Responce to my order
        ToDo: add order to history if successful
        """
        self._logger.info(f"Got reply msg: {msg}")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_reply', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_reply(msg)

    def on_heartbeat(self):
        """
        Heartbeating reaction
        """
        self._logger.debug("Got heart beat")
        for s in set(filter(lambda ss: callable(getattr(ss, 'on_heartbeat', None)), self._subscribers)):
            # todo: refactor to data classes instead of quik msg
            s.on_heartbeat()
