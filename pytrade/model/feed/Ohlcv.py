from dataclasses import dataclass
from datetime import datetime

from model.feed.Asset import Asset


@dataclass
class Ohlcv:
    """
    Candle open, high, low, close, volume with datetime
    """
    dt: datetime
    asset: Asset
    o: float
    h: float
    l: float
    c: float
    v: float
