import logging

from connector.quik.WebQuikConnector import WebQuikConnector

class WebQuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """
    _logger = logging.getLogger(__name__)

    def __init__(self, connector: WebQuikConnector):
        self._connector = connector
        self._connector.broker = self
        self._callbacks = {}
        self._broker_subscribers = {}

    def subscribe_broker(self, subscriber):
        """
        Subscribe to broker events - trades, account etc.
        :param subscriber broker class, inherited from broker'
        """
        # Register given feed callback
        self._broker_subscribers.add(subscriber)

    def on_message(self, msg):
        callback = self._callbacks.get(msg['msgid'])
        if callback:
            callback(msg)

    def buy(self, class_code, sec_code, price, quantity):
        """
        Send buy order to broker
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='B', price=price, quantity=quantity)

    def sell(self, class_code, sec_code, price, quantity):
        """
        Send sell order to broker
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='S', price=price, quantity=quantity)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        """
        self._quik.kill_all_orders('SPBFUT', 'RIU8')

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
