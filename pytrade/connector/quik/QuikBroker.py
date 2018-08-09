from pytrade.connector.quik.QuikConnector import QuikConnector
import logging
from enum import Enum


class QuikBroker:
    """
    Broker facade for QuikConnector. Orders, account info etc.
    """

    def __init__(self, quik):
        self._quik = quik
        self._quik.broker_callbacks.append(self.on_account_info())
        self._quik.heartbeat_callbacks.add(self.on_heartbeat)

    def start(self):
        """
        Starting QuikConnector loop if not done yet
        :return:
        """
        self._logger.info("Starting quik broker")
        if self._quik.status == QuikConnector.Status.DISCONNECTED:
            self._quik.run()

    def buy(self, class_code, sec_code, price, quantity):
        """
        Send buy order to broker
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :return:
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='B', price=price, quantity=quantity)

    def sell(self, class_code, sec_code, price, quantity):
        """
        Send sell order to broker
        :param class_code security class, example 'SPBFUT'
        :param sec_code code of security, example 'RIU8'
        :return:
        """
        self._quik.send_order(class_code=class_code, sec_code=sec_code, operation='S', price=price, quantity=quantity)

    def kill_all_orders(self):
        """
        Kill all orders in trade system
        :return:
        """
        self._quik.kill_all_orders('SPBFUT', 'RIU8')

    def on_account_info(self):
        """
        Account information changed callback
        """
        print("Account info received")

    def on_heartbeat(self):
        """
        Heartbeating reaction
        :return:
        """
