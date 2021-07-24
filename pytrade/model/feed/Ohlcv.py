from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ohlcv:
    """
    Candle open, high, low, close, volume with datetime
    """
    dt: datetime
    o: float
    h: float
    l: float
    c: float
    v: float
