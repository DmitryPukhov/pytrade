import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    """
    Asset code and name
    """
    class_code: str
    sec_code: str

    def __str__(self):
        return f"{self.class_code}/{self.sec_code}"

    @staticmethod
    def of(strval: str):
        return Asset(*strval.split("/"))

    @staticmethod
    def any_asset():
        return Asset("*", "*")
