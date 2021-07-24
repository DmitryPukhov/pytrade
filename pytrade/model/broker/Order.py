from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Order:
    number: str
    dt: datetime
    class_code: str
    sec_code: str
    is_sell: bool
    account: str
    price: float
    quantity: int
    volume: float
    status: str
