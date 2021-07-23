from dataclasses import dataclass
from datetime import datetime

from sortedcontainers import SortedList


@dataclass
class Level2:
    """
    All level2 quotes at the moment
    """
    dt: datetime
    # Level 2 items price: bid or ask, sorted by price
    items: SortedList = SortedList(key=lambda item: item.price)
