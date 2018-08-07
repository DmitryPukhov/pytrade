import logging


class Strategy:
    """
    Strategy receives data from feed and make orders to broker
    """
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)

    def __init__(self, feed, broker):
        self._feed = feed

        # Connecting to broker
        self._broker = broker

        # Connecting to feed
        self._feed.tick_callbacks.add(self.on_tick)
        self._feed.heartbeat_callbacks.add(self.on_heartbeat)
        self._heart_beating = False
        self._flag = False

    def on_tick(self, class_code, sec_code, price, vol):
        """
        New price/vol tick received
        :return None
        """
        self._logger.info('Tick receved. sec_code: %s, price: %s, vol:%s' % (sec_code, price, vol))
        # if not self._flag and sec_code == 'RIU8':
        #     self._broker.sell(class_code='SPBFUT', sec_code='RIU8', price=price - 50, quantity=1)
        #     self._flag = True

    def on_heartbeat(self):
        """
        Heartbeat received
        :return: None
        """
        # if not self._heart_beating:
        #     # Action during first heartbeat
        #     self._broker.kill_all_orders()
        #
        # self._heart_beating = True
