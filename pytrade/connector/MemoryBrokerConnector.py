import logging


class MemoryBrokerConnector:
    """
    Broker emulator, keeps all trades in memory
    """

    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Init{__name__}")
        self.client_code = None
        self.trade_account = None
        self._broker_subscribers = []

    def subscribe_broker(self, subscriber):
        self._broker_subscribers.append(subscriber)

    def run(self):
        return

    def buy(self, class_code, sec_code, price, quantity):
        self._logger.info(f"Got buy command. class_code:{class_code}, sec_code: {sec_code}, "
                          f"price: {price}, quantity: {quantity}")
        #self._broker_connector.buy(class_code, sec_code, price, quantity)

    def sell(self, class_code, sec_code, price, quantity):
        self._logger.info(f"Got sell command. class_code:{class_code}, sec_code: {sec_code}, "
                          f"price: {price}, quantity: {quantity}")
        #self._broker_connector.sell(class_code, sec_code, price, quantity)

