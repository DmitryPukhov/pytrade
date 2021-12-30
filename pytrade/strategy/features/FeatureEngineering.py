import datetime
import logging

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from strategy.features.Level2Features import Level2Features
from strategy.features.PriceFeatures import PriceFeatures
from strategy.features.TargetFeatures import TargetFeatures


class FeatureEngineering:

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def features_of(self, quotes: pd.DataFrame, level2: pd.DataFrame, period: int, freq: str, size: int,
                    l2size: int = 0,
                    l2buckets: int = 20) -> (pd.DataFrame, pd.DataFrame):
        """ Feature engineering from quotes and level2"""
        self._logger.info("Starting feature engineering")
        level2_features = Level2Features().level2_buckets(level2, l2size, l2buckets)
        price_features = PriceFeatures().minmax_past(quotes, period, freq, size)
        features = pd.merge_asof(price_features, level2_features, left_on="datetime", right_on="datetime",
                                 tolerance=pd.Timedelta("1 min"))
        time_features = self.time_features(features)
        features = features.join(time_features).set_index("datetime")
        features.replace([np.inf, -np.inf], np.nan, inplace=True)
        features.dropna(inplace=True)
        target = TargetFeatures().min_max_future(quotes, 5, 'min').loc[features.index, :]
        target.replace([np.inf, -np.inf], np.nan, inplace=True)
        target.dropna(inplace=True)
        features = features.loc[target.index,:]
        #X = MinMaxScaler(feature_range=(0, 1)).fit_transform(features.values)
        # y = MinMaxScaler(feature_range=(0, 1)).fit(target.values)
        self._logger.info("Completed feature engineering")
        return features, target

    def time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add day, week to features
        :param df: dataframe with datetime column
        :return: dataframe with time features
        """
        df2 = pd.DataFrame(index=df.index)
        df2["dayofweek"] = df['datetime'].dt.dayofweek
        df2["month"] = df['datetime'].dt.month
        df2["year"] = df['datetime'].dt.year
        df2["hour"] = df['datetime'].dt.hour
        df2["minute"] = df['datetime'].dt.minute
        df2["sec"] = df['datetime'].dt.second
        return df2
