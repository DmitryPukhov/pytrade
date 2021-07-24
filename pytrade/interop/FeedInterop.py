import logging

import pika
from connector.quik.MsgId import MsgId
from connector.quik.QueueName import QueueName
from model.feed.Asset import Asset
from model.feed.Ohlcv import Ohlcv


class FeedInterop:
    """
    Get data from feed and publish it to rabbitmq for interop with external systems
    """

    def __init__(self, feed, rabbit_host: str):
        self._logger = logging.getLogger(__name__)
        self._feed = feed

        # Subscribe to feed
        self.callbacks = {
            # MsgId.QUOTES: self._on_quotes,
            MsgId.GRAPH: self.on_candle,
            # MsgId.LEVEL2: self._on_level2,
        }
        self._feed.subscribe_feed(Asset("*", "*"), self)

        # Init rabbitmq connection
        self._rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
        self._rabbit_channel = self._rabbit_connection.channel()
        for q in [QueueName.CANDLES]:
            self._logger.info(f"Declaring rabbit queue {q}")
            self._rabbit_channel.queue_declare(queue=q, durable=True)

    def on_candle(self, asset: Asset, ohlcv: Ohlcv):
        """
        Receive ohlc data and transfer to rabbit mq for interop
        :param data: dict like {"msgid":21016,"graph":{"QJSIM\u00A6SBER\u00A60":[{"d":"2019-10-01
        10:02:00","o":22649,"c":22647,"h":22649,"l":22646,"v":1889}]}} :return:
        """

        self._logger.debug(f'Got feed: {asset}, {ohlcv}')
        # ohlcv = {'d': str(dt), 'o': ohlcv, 'h': h, 'l': l_, 'c': c, 'v': asset}
        # self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.CANDLES, body=str(ohlcv))
        asset_ohlcv = {'asset': str(asset), 'dt': str(ohlcv.dt), 'o': ohlcv.o, 'h': ohlcv.h, 'l': ohlcv.l, 'c': ohlcv.c,
                       'v': ohlcv.v}
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.CANDLES, body=str(asset_ohlcv))
