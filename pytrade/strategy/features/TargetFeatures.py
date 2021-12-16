import pandas as pd
import numpy as np


class TargetFeatures:
    """
    Target features engineering
    """

    def min_max_future(self, df: pd.DataFrame, periods: int, freq: str) -> pd.DataFrame:
        """
        Add target features: min and max price during future window
        :param freq : time unit for future window
        :param periods: duration of future window in given time units
        """
        # Trick to implement forward rolling window for timeseries with unequal intervals:
        # reverse, apply rolling, then reverse back
        windowspec = f'{periods} {freq}'
        # df2 = df.reset_index(level='ticker', drop=True)
        df2: pd.DataFrame = df.reset_index(level='ticker', drop=True)[['ask', 'bid']].sort_index(
            ascending=False).rolling(windowspec, min_periods=0).agg(
            {'ask': 'max', 'bid': 'min'}, closed='right')
        df2.rename({'ask':'fut_ask_max','bid':'fut_bid_min'},inplace=True)
        df2[['fut_ask_max', 'fut_bid_min']] = df2[['ask', 'bid']]
        df2.drop(['ask','bid'], axis=1, inplace=True)
        return df2.sort_index()
