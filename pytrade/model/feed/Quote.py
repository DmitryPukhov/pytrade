from dataclasses import dataclass
from datetime import datetime

from model.feed.Asset import Asset


@dataclass
class Quote:
    """
    Quote with dt,asset,bid,ask,last,last change
    """
    dt: datetime
    asset: Asset
    bid: float
    ask: float
    last: float
    last_change: float
