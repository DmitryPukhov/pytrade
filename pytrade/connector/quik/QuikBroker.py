from pytrade.connector.quik.QuikConnector import QuikConnector
import logging


class QuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self, quik):
        self._quik: QuikConnector = quik

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """
        self._logger.info("Starting quik broker")
        if self._quik.status == QuikConnector.Status.DISCONNECTED:
            self._quik.run()

    def buy(self, class_code, sec_code):
        """
        Send buy order to broker
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :return:
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='B', price=0, quantity=1)

    def sell(self, class_code, sec_code):
        """
        Send sell order to broker
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :return:
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='S', price=0, quantity=1)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        :return:
        """
        self._quik.kill_all_orders()


