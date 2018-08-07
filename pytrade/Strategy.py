import logging


class Strategy:
    """
    Strategy receives data from feed and make orders to broker
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, broker, sec_class, sec_code):
        self._feed = feed
        self.sec_class = sec_class
        self.sec_code = sec_code

        # Connecting to broker
        self._broker = broker

        # Connecting to feed
        self._feed.tick_callbacks.add(self.on_tick)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False
        self._flag = False

    def on_tick(self, asset_exchange, asset_code, price, vol):
        """
        New price/vol tick received
        @param asset_exchange exchange SPBFUT for
        :return None
        """
        self._logger.info('Tick receved. sec_class: %s, sec_code: %s, price: %s, vol:%s' % (
            self.sec_class, self.sec_code, price, vol))

        #if not self._flag and self.sec_code == 'RIU8':
            #self._broker.buy(class_code='SPBFUT', sec_code='RIU8', price=price + 50, quantity=1)
            #self._broker.sell(class_code=self.sec_class, sec_code=self.sec_code, price=price-100, quantity=1)
            #self._flag = True

    def on_heartbeat(self):
        """
        Heartbeat received
        :return: None
        """
        #if not self._flag and self.sec_code == 'RIU8':
            #self._broker.buy(class_code='SPBFUT', sec_code='RIU8', price=114500, quantity=3)
            #self._broker.sell(class_code=self.sec_class, sec_code=self.sec_code, price=114400, quantity=4)
            #self._flag = True
