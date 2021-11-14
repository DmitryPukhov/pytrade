from dataclasses import dataclass
from datetime import datetime
from typing import List

from sortedcontainers import SortedList

from model.feed.Asset import Asset
from model.feed.Level2Item import Level2Item


@dataclass
class Level2:
    """
    All level2 quotes at the moment
    """
    dt: datetime
    asset: Asset
    # Level 2 items price: bid or ask, sorted by price
    items: List[Level2Item] = SortedList(key=lambda item: item.price)

    @staticmethod
    def of(dt: datetime, asset: str, items: List[Level2Item]):
        return Level2(dt, asset, SortedList(items, key=lambda item: item.price))
