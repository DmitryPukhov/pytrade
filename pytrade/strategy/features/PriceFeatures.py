import pandas as pd
import numpy as np


class PriceFeatures:
    """
    Price features engineering
    """

    def minmax_past(self, quotes: pd.DataFrame, period: int, freq: str, size: int) -> pd.DataFrame:
        """
        Quotes and candles features
        :param period:
        """
        # Drop asset column (we have only one asset) and resample to given intervals
        quotes = quotes.droplevel(1)
        windowspec = f"{period} {freq}"
        rolling = quotes.rolling(windowspec, min_periods=0).agg(
            {'ask': 'max', 'bid': 'min'}, closed='right')
        # Add previous intervals lows/highs
        df2 = pd.DataFrame(index=quotes.index)
        for shift in range(1, size + 1):
            df2[[f"-{shift}*{period}{freq}_high", f"-{shift}*{period}{freq}_low"]] = \
                rolling.shift(shift - 1, freq)[['ask', 'bid']] \
                    .reindex(df2.index, method='nearest', tolerance=windowspec)
        return df2.sort_index()
    #
    # def minmax_past2(self, quotes: pd.DataFrame, periods: int, freq: str, size) -> pd.DataFrame:
    #     """
    #     Quotes and candles features
    #     """
    #     # Drop asset column (we have only one asset) and resample to given intervals
    #     rule = f"{periods} {freq}"
    #     resampled = quotes.droplevel(1).resample(rule, closed='right', label='right')
    #     df = pd.DataFrame()
    #     df['max'] = resampled['ask'].max()
    #     df['min'] = resampled['bid'].min()
    #
    #     for shift in range(1, size + 1):
    #         df[f"-{shift}*{periods}{freq}_max"] = df.shift(shift - 1)['max']
    #         df[f"-{shift}*{periods}{freq}_min"] = df.shift(shift - 1)['min']
    #     df.drop(columns=['min', 'max'], inplace=True)
    #     return df
