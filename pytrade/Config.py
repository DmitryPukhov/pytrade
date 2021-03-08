class Config:
    """
    Application configuration
    """

    # Web quik config
    server = 'junior.webquik.ru'
    conn = 'wss://' + server + ':443/quik'

    # Account and password, provided by broker
    account = 'U1234567'
    passwd = '1234'

    # Client code, provided by broker
    client_code = '10113'
    # Trade account for specific market. Can be seen as "firm" or "account" column in quik tables
    trade_account = "NL0011100043"

    # Main asset to trade
    sec_class = 'QJSIM'
    sec_code = 'SBER'
