import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    """
    Asset code and name
    """
    class_code: str
    sec_code: str
