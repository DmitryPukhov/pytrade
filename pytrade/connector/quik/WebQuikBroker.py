import logging

from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.MsgId import MsgId


class WebQuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, connector: WebQuikConnector):
        # 21001:"Заявки",
        # 21003:"Сделки",
        # 21004:"Денежн.лимиты"
        # 21005:"Бумаж.лимиты",
        self.callbacks = {
            MsgId.ORDERS: self.on_orders,
            MsgId.TRADES: self.on_trades,
            MsgId.TRADE_ACCOUNTS: self.on_trade_accounts,
            MsgId.TRADES_FX: self.on_trades_fx,
            MsgId.MONEY_LIMITS: self.on_money_limits,
            MsgId.STOCK_LIMITS: self.on_stock_limits,
            MsgId.LIMIT_HAS_RECEIVED: self.on_limit_received}
        self._connector = connector
        self._connector.subscribe(self.callbacks)
        self._broker_subscribers = {}

    def on_trades_fx(self, msg):
        self._logger.info(f"On trades fx. msg={msg}")

    def on_trade_accounts(self, msg):
        self._logger.info(f"On trade accounts. msg={msg}")

    def on_orders(self, msg):
        self._logger.info(f"On orders. msg={msg}")

    def on_trades(self, msg):
        self._logger.info(f"On trades. msg={msg}")

    def on_money_limits(self, msg):
        self._logger.info(f"On money limits. msg={msg}")

    def on_stock_limits(self, msg):
        self._logger.info(f"On stock limits. msg={msg}")

    def on_limit_received(self, msg):
        self._logger.info(f"Limit has received. msg={msg}")

    def subscribe_broker(self, subscriber):
        """
        Subscribe to broker events - trades, account etc.
        :param subscriber broker class, inherited from broker'
        """
        # Register given feed callback
        self._broker_subscribers.add(subscriber)

    def buy(self, class_code, sec_code, price, quantity):
        """
        Send buy order to broker
        """
        raise NotImplementedError
        # self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='B', price=price, quantity=quantity)

    def sell(self, class_code, sec_code, price, quantity):
        """
        Send sell order to broker
        """
        raise NotImplementedError
        # var g={ccode:f.ccode,scode:d.down("#symbol").getScode(),secType:f.secType,account:d.down("#account").getValue(),clientCode:c,settleDate:d.down("#settleDate").getNoDelimValue(),buySell:e?"B":"S",price:a==="M"?0:d.down("#rate").getValue(),qty:toNumVolume(d.down("#amount").getValue()),slippage:b?b:0,limitMarket:a,execution:d.down("#execution").getValue(),comment:c+"/"+d.down("#comment").getValue(),currency:f.currency};
        # self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='S', price=price, quantity=quantity)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        """
        raise NotImplementedError
        # self._quik.kill_all_orders('SPBFUT', 'RIU8')

    def on_heartbeat(self):
        """
        Heartbeating reaction
        """
        for subscriber in self._broker_subscribers:
            subscriber.on_heartbeat()
