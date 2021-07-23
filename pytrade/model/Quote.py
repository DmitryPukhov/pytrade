from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quote:
    """
    Candle open, high, low, close, volume with datetime
    """
    dt: datetime
    bid: float
    ask: float
    last: float
    last_change: float
