import json
import logging
from threading import Thread
from pika import BlockingConnection, ConnectionParameters

from broker.Broker import Broker
from connector.quik.QueueName import QueueName
from connector.quik.WebQuikBroker import WebQuikBroker
from model.broker.Order import Order


class BrokerInterop:
    """
    Broker facade for QuikConnector. Holds account info, can  make orders.
    Supports only simple buy/sell at the moment
    Todo: add different types of orders: stop, market ...
    """

    def __init__(self, broker: Broker, rabbit_host: str):
        self._logger = logging.getLogger(__name__)
        self._rabbit_host = rabbit_host
        self._broker = broker
        self._broker.subscribe_broker(self)

        # Init rabbit mq
        self._logger.info(f"Init rabbit connection to {rabbit_host}")
        self._rabbit_connection = BlockingConnection(ConnectionParameters(rabbit_host))
        # self._rabbit_connection = pika.connection.Connection(pika.ConnectionParameters(rabbit_host))
        self._rabbit_channel = self._rabbit_connection.channel()
        for q in [QueueName.TRADE_ACCOUNT,
                  QueueName.ORDERS,
                  QueueName.TRADES,
                  QueueName.MONEY_LIMITS,
                  QueueName.STOCK_LIMITS
                  ]:
            self._logger.info(f"Declaring rabbit queue {q}")
            self._rabbit_channel.queue_declare(queue=q, durable=True)

        # Subscribe to buy/sell events in new thread because pika consumes synchronously only
        self._consumer_rabbit_connection = None
        self._consumer_rabbit_channel = None
        Thread(target=self.listen_commands).start()

        self._logger.info("Initialized")

    def listen_commands(self):
        """
        Consuming buy/sell commands from rabbit
        """
        self._consumer_rabbit_connection = BlockingConnection(ConnectionParameters(self._rabbit_host))
        self._consumer_rabbit_channel = self._consumer_rabbit_connection.channel()

        # Listen buy/sell orders from external system
        self._listen_queue(QueueName.CMD_BUYSELL, self.on_cmd_buysell)
        self._listen_queue(QueueName.MSG_RAW, self.on_raw_msg)
        # self._logger.info(f"Declaring rabbit queue {QueueName.CMD_BUYSELL}")
        # self._consumer_rabbit_channel.queue_declare(queue=QueueName.CMD_BUYSELL, durable=True, auto_delete=True)
        # self._logger.info(f"Consiming to rabbit queue {QueueName.CMD_BUYSELL}")
        # self._consumer_rabbit_channel.basic_consume(QueueName.CMD_BUYSELL, self.on_cmd_buysell,
        #                                             consumer_tag="WebQuikBroker")
        self._consumer_rabbit_channel.start_consuming()

    def _listen_queue(self, queue, callback):
        """
        Add a listener callback to get buy/sell or raw commands from rabbit
        """
        # Listen buy/sell orders from external system
        self._logger.info(f"Declaring rabbit queue {queue}")
        self._consumer_rabbit_channel.queue_declare(queue=queue, durable=True, auto_delete=True)
        self._logger.info(f"Declaring callback to rabbit queue: {queue}, callback: {callback}")
        self._consumer_rabbit_channel.basic_consume(queue, callback,
                                                    consumer_tag=queue)

    def on_order_answer(self, msg):
        self._logger.info(f"Got msg: {msg}")

    def on_raw_msg(self, channel, method_frame, header_frame, rawmsg):
        self._logger.debug(f"Got raw msg {rawmsg}")
        self._broker.send_raw_msg(rawmsg.decode())

    def on_cmd_buysell(self, channel, method_frame, header_frame, rawmsg):
        self._logger.info(f"Got buy/sell command. msg={rawmsg}")
        msg = json.loads(rawmsg)
        if msg["operation"] == "buy":
            self._broker.buy(msg['secClass'], msg['secCode'], msg['price'], msg['quantity'])
        elif msg["operation"] == "sell":
            self._broker.sell(msg['secClass'], msg['secCode'], msg['price'], msg['quantity'])
        else:
            self._logger.error(f"Operation should be buy or sell in command: {msg}")

    def on_trades_fx(self, msg):
        self._logger.debug(f"On trades fx. msg={msg}")

    def on_trade_accounts(self, msg):
        # Information about my account. Usually one for stocks, one for futures.
        # {"msgid":21022,"trdacc":"NL0011100043","firmid":"NC0011100000","classList":["QJSIM"],"mainMarginClasses":["QJSIM"],"limitsInLots":0,"limitKinds":["0","1","2"]}
        # Just push the message to rabbitmq
        self._logger.debug(f"On trade accounts. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.TRADE_ACCOUNT, body=str(msg))

    def on_orders(self, order: Order):
        # Information about my orders
        self._logger.debug(f"Got orders from broker: {order}")
        msg = json.dumps(order.__dict__, default=str)
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.ORDERS, body=msg)

    def on_trades(self, msg):
        self._logger.debug(f"On trades. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.TRADES, body=str(msg))

    def on_money_limits(self, msg):
        self._logger.debug(f"On money limits. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.MONEY_LIMITS, body=str(msg))

    def on_stock_limits(self, msg):
        self._logger.debug(f"On stock limits. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.STOCK_LIMITS, body=str(msg))

    def on_limit_received(self, msg):
        self._logger.debug(f"Limit has received. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.STOCK_LIMIT, body=str(msg))

    def subscribe_broker(self, subscriber):
        """
        Subscribe to broker events - trades, account etc.
        :param subscriber broker class, inherited from broker'
        """
        # Register given feed callback
        self._broker_subscribers.add(subscriber)

    def on_trans_reply(self, msg: str):
        """
        Responce to my order
        ToDo: add order to history if successful
        """
        self._logger.info(f"Got msg: {msg}")

    def on_heartbeat(self):
        """
        Heartbeating reaction
        """
        for subscriber in self._broker_subscribers:
            subscriber.on_heartbeat()
