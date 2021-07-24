class QueueName(object):
    """
    Rabbit queue names
    """
    TRADE_ACCOUNT = "pytrade.broker.trade.account"
    ORDERS = "pytrade.broker.orders"
    CMD_BUYSELL = "pytrade.broker.cmd.buysell"
    MSG_RAW = "pytrade.broker.msg.raw"
    MSG_REPLY = "pytrade.broker.msg.reply"
    TRADES = "pytrade.broker.trades"
    MONEY_LIMITS = "pytrade.broker.money.limits"
    STOCK_LIMITS = "pytrade.broker.stock.limits"
    LIMIT = "pytrade.broker.stock.limit"
    CANDLES = "pytrade.feed.candles"
