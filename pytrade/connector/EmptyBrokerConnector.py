import logging


class EmptyBrokerConnector:
    """
    Empty stub for broker when application needs only feed
    """

    def __init__(self, config):
        self._logger = logging.getLogger(__name__)
        self._logger.info(f"Init{__name__}")
        self.client_code = None
        self.trade_account = None

    def subscribe_broker(self, subscriber): return

    def run(self): return
