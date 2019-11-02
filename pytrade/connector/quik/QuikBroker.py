import logging


class QuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """
    _logger = logging.getLogger(__name__)

    def __init__(self, quik):
        self._quik = quik
        self._quik.broker_callbacks.append(self.on_account_info())
        self._quik.heartbeat_callbacks.add(self.on_heartbeat)

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        """
        self._logger.info("Starting quik broker")
        self._quik.start()

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
        :return:
        """
