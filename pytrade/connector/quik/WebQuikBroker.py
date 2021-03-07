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
        self._connector = connector
        self._connector.broker = self
        self._broker_subscribers = {}

    def on_trade_session_open(self, msg):
        self._logger.info("Broker trade session opened. msg_id = %s", msg['msgid'])
        ##msg = '{"msgid": %s}' % (11004)
        ##self._connector.send(msg)
        # self._logger.info('Requesting account  for %s\\%s', class_code, sec_code)
        # msg = '{"msgid":%s,"c":"%s","s":"%s","p":%s}' % (MsgId.MSG_ID_CREATE_DATASOURCE, class_code, sec_code, 0)

    def subscribe_broker(self, subscriber):
        """
        Subscribe to broker events - trades, account etc.
        :param subscriber broker class, inherited from broker'
        """
        # Register given feed callback
        self._broker_subscribers.add(subscriber)

    def on_message(self, msg):
        self._logger.debug("Got message: %s", msg)
        # callback = self._callbacks.get(msg['msgid'])
        # if callback:
        #     callback(msg)

    def buy(self, class_code, sec_code, price, quantity):
        """
        Send buy order to broker
        """
        raise NotImplementedError
        #self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='B', price=price, quantity=quantity)

    def sell(self, class_code, sec_code, price, quantity):
        """
        Send sell order to broker
        """
        raise NotImplementedError
        #var g={ccode:f.ccode,scode:d.down("#symbol").getScode(),secType:f.secType,account:d.down("#account").getValue(),clientCode:c,settleDate:d.down("#settleDate").getNoDelimValue(),buySell:e?"B":"S",price:a==="M"?0:d.down("#rate").getValue(),qty:toNumVolume(d.down("#amount").getValue()),slippage:b?b:0,limitMarket:a,execution:d.down("#execution").getValue(),comment:c+"/"+d.down("#comment").getValue(),currency:f.currency};
        #self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='S', price=price, quantity=quantity)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        """
        raise NotImplementedError
        #self._quik.kill_all_orders('SPBFUT', 'RIU8')

    def on_account_info(self):
        """
        Account information changed callback
        """
        self._logger.info("Account info received")

    def on_heartbeat(self):
        """
        Heartbeating reaction
        """
        for subscriber in self._broker_subscribers:
            subscriber.on_heartbeat()
