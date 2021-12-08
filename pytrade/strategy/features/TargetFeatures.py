import pandas as pd
import numpy as np


class TargetFeatures:
    """
    Target features preparation
    """
    def with_min_max_future(self, df: pd.DataFrame, periods: int, freq: str) -> pd.DataFrame:
        """
        For given price/level2 data prepare target features
        """
        # Trick to implement forward rolling window for timeseries with unequal intervals:
        # reverse, apply rolling, then reverse back
        windowspec = f'{periods} {freq}'
        df2 = df[['ask', 'bid']].sort_index(ascending=False).rolling(windowspec, min_periods=0).agg(
            {'ask': 'max', 'bid': 'min'}, closed='right')
        df[['fut_ask_max', 'fut_bid_min']] = df2[['ask', 'bid']]
        return df