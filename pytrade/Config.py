class Config:
    """
    Application configuration
    """

    # Web quik config
    server = 'junior.webquik.ru'
    conn = 'wss://' + server + ':443/quik'
    account = 'U1234567'
    passwd = '12345'

    # Main asset
    sec_class = 'TQBR'
    sec_code = 'GAZP'
