import logging
from datetime import datetime

import pika
from connector.quik.MsgId import MsgId
from connector.quik.QueueName import QueueName


class BrokerInterop:
    """
    Get data from broker and publish it to rabbitmq for interop with external systems
    Get order messages from rabbit and send them to a broker
    """

    def __init__(self, feed, rabbit_host: str):
        self._logger = logging.getLogger(__name__)
        self._feed = feed

        # Subscribe to feed
        self.callbacks = {
                          #MsgId.QUOTES: self._on_quotes,
                          MsgId.GRAPH: self._on_candle,
                          #MsgId.LEVEL2: self._on_level2,
                          }
        self._feed.subscribe(self.callbacks)

        # Init rabbitmq connection
        self._rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
        self._rabbit_channel = self._rabbit_connection.channel()
        for q in [QueueName.CANDLES]:
            self._logger.info(f"Declaring rabbit queue {q}")
            self._rabbit_channel.queue_declare(queue=q, durable=True)

    def _on_candle(self, data: dict):
        """
        Receive ohlc data and transfer to rabbit mq for interop
        :param data: dict like {"msgid":21016,"graph":{"QJSIM\u00A6SBER\u00A60":[{"d":"2019-10-01
        10:02:00","o":22649,"c":22647,"h":22649,"l":22646,"v":1889}]}} :return:
        """
        self._logger.debug('Got feed: %s', data)

        # Todo: get rid of nested check
        for asset_str in data['graph'].keys():
            # Each asset in data['graph']
            (asset_class, asset_code) = self._connector.asset2tuple(asset_str)
            if self._feed_subscribers[(asset_class, asset_code)] is not None:
                asset_data = data['graph'][asset_str]
                for ohlcv in asset_data:
                    # Each ohlcv for this asset
                    # dt = datetime.fromisoformat(ohlcv['d'])
                    # o = ohlcv['o']
                    # h = ohlcv['h']
                    # l_ = ohlcv['l']
                    # c = ohlcv['c']
                    # v = ohlcv['v']
                    # Send the candle to rabbitmq
                    self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.CANDLES, body=str(ohlcv))
