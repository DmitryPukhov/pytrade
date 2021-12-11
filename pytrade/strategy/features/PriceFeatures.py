import pandas as pd
import numpy as np


class PriceFeatures:
    """
    Price features engineering
    """

    def prices(self, quotes: pd.DataFrame) -> pd.DataFrame:
        """
        Quotes and candles features
        """
        #df = quotes[['ask', 'bid']][-1]
        return quotes
