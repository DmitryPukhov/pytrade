import json
import logging
import random
from threading import Thread

import pika

from connector.quik.QueueName import QueueName
from connector.quik.WebQuikConnector import WebQuikConnector
from connector.quik.MsgId import MsgId


class WebQuikBroker:
    """
    Broker facade for QuikConnector. Holds account info, can  make orders.
    Supports only simple buy/sell at the moment
    Todo: add different types of orders: stop, market ...
    """

    def __init__(self, connector: WebQuikConnector, client_code, trade_account, rabbit_host):
        self._logger = logging.getLogger(__name__)

        self.client_code = client_code
        self.trade_account = trade_account
        # 21001:"Заявки",
        # 21003:"Сделки",
        # 21004:"Денежн.лимиты"
        # 21005:"Бумаж.лимиты",
        self.callbacks = {
            MsgId.ORDERS: self.on_orders,
            MsgId.TRADES: self.on_trades,
            MsgId.TRADE_ACCOUNTS: self.on_trade_accounts,
            MsgId.TRADES_FX: self.on_trades_fx,
            MsgId.MONEY_LIMITS: self.on_money_limits,
            MsgId.STOCK_LIMITS: self.on_stock_limits,
            MsgId.LIMIT_HAS_RECEIVED: self.on_limit_received}
        self._connector = connector
        self._connector.subscribe(self.callbacks)
        self._broker_subscribers = {}
        # accounts dictionary class_code -> account info
        # Usually different accounts for securities, futures, forex ??

        # Init rabbit mq
        self._logger.info(f"Init rabbit connection to {rabbit_host}")
        self._rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host))
        #self._rabbit_connection = pika.connection.Connection(pika.ConnectionParameters(rabbit_host))
        self._rabbit_channel = self._rabbit_connection.channel()
        for q in [QueueName.TRADE_ACCOUNT,
                  QueueName.ORDERS,
                  QueueName.TRADES,
                  QueueName.MONEY_LIMITS,
                  QueueName.STOCK_LIMITS
                  ]:
            self._logger.info(f"Declaring rabbit queue {q}")
            self._rabbit_channel.queue_declare(queue=q, durable=True)

        self._logger.info(f"Declaring rabbit queue {QueueName.CMD_BUYSELL}")
        self._rabbit_channel.queue_declare(queue=QueueName.CMD_BUYSELL, durable=True, auto_delete=True)

        # Subscribe to buy/sell events
        self._logger.info(f"Consiming to rabbit queue {QueueName.CMD_BUYSELL}")
        self._rabbit_channel.basic_consume(QueueName.CMD_BUYSELL, self.on_cmd_buysell, consumer_tag="WebQuikBroker")
        #self._rabbit_channel.start_consuming()
        self._logger.info("Initialized")

    def on_cmd_buysell(self, channel, method_frame, header_frame, msg):
        self._logger.info(f"Got buy/sell command. msg={msg}")

    def on_trades_fx(self, msg):
        self._logger.debug(f"On trades fx. msg={msg}")

    def on_trade_accounts(self, msg):
        # Information about my account. Usually one for stocks, one for futures.
        # {"msgid":21022,"trdacc":"NL0011100043","firmid":"NC0011100000","classList":["QJSIM"],"mainMarginClasses":["QJSIM"],"limitsInLots":0,"limitKinds":["0","1","2"]}
        # Just push the message to rabbitmq
        self._logger.debug(f"On trade accounts. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.TRADE_ACCOUNT, body=str(msg))

    def on_orders(self, msg):
        # Information about my orders
        self._logger.debug(f"On orders. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.ORDERS, body=msg)

    def on_trades(self, msg):
        self._logger.debug(f"On trades. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.TRADES, body=msg)

    def on_money_limits(self, msg):
        self._logger.debug(f"On money limits. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.MONEY_LIMITS, body=msg)

    def on_stock_limits(self, msg):
        self._logger.debug(f"On stock limits. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.STOCK_LIMITS, body=msg)

    def on_limit_received(self, msg):
        self._logger.debug(f"Limit has received. msg={msg}")
        self._rabbit_channel.basic_publish(exchange='', routing_key=QueueName.STOCK_LIMIT, body=msg)

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
        # Successful transaction should look like this:
        # {"msgid":21009,"request":1,"status":3,"ordernum":5736932911,"datetime":"2021-03-08 22:05:35","text":"(161) Заявка N 5736932911 зарегистрирована. Удовлетворено 1"}
        self._logger.info(f"Got msg {msg}")

    def test(self):
        msgdict = {
            "transid": random.randint(1, 147483647),
            "msgid": MsgId.ORDER,
            "action": "SIMPLE_STOP_ORDER",
            "MARKET_STOP_LIMIT": "YES",

            "ccode": self.class_code,
            "scode": self.sec_code,
            "operation": "B",

            "quantity": 1,
            "clientcode": self.client_code,
            "account": self.trade_account,
            "stopprice": 215
        }
        msg = json.dumps(msgdict)
        return msg

    def get_order_msg(self, class_code: str, sec_code: str, is_buy: bool, price: float, quantity: int) -> str:
        """
        Prepares buy or sell order json for quik
        """
        msgdict = {
            "transid": random.randint(1, 2 ^ 64),
            "msgid": MsgId.ORDER,
            "ccode": class_code,
            "scode": sec_code,
            "sell": 0 if is_buy else 1,
            "quantity": quantity,
            "clientcode": self.client_code,
            "account": self.trade_account,
            "price": price
        }
        msg = json.dumps(msgdict)
        return msg

    def buy(self, class_code, sec_code, price, quantity):
        """
        Send buy order to broker
        """
        msg = self.get_order_msg(class_code=class_code, sec_code=sec_code, is_buy=True, price=price, quantity=quantity)
        self._logger.info(f"Sending buy message {msg}")
        self._connector.send(msg)

    def sell(self, class_code, sec_code, price, quantity):
        """
        Send sell order to broker
        """
        msg = self.get_order_msg(class_code=class_code, sec_code=sec_code, is_buy=False, price=price, quantity=quantity)
        self._logger.info(f"Sending sell message {msg}")
        self._connector.send(msg)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        """
        raise NotImplementedError

    def on_heartbeat(self):
        """
        Heartbeating reaction
        """
        for subscriber in self._broker_subscribers:
            subscriber.on_heartbeat()
