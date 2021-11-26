import pandas as pd
import numpy as np


class Preprocess:
    """
    Market data cleaning, imputing, feature extraction.
    """

    def level2_features(self, level2: pd.DataFrame, l2size: int = 0, buckets: int = 0) -> pd.DataFrame:
        """
        Return dataframe with level2 feature columns. Colums are named "bucket<n>"
        where n in a number of price interval and value is summary volumes inside this price.
        For ask price intervals number of buckets >0, for bid ones < 0
        level2: DataFrame with level2 tick columns: datetime, price, bid_vol, ask_vol
        level2 price and volume for each time
        """

        # Calc middle price between ask and bid
        level2 = level2.set_index("datetime")
        askmin = level2[level2['ask_vol'].notna()].groupby('datetime')['price'].min().reset_index().set_index(
            "datetime")
        level2['price_min'] = askmin['price']
        bidmax = level2[level2['bid_vol'].notna()].groupby('datetime')['price'].max().reset_index().set_index(
            "datetime")
        level2['price_max'] = bidmax['price']
        level2['price_middle'] = (askmin['price'] + bidmax['price']) / 2

        # Assign a bucket number to each level2 item
        # scalar level2 size and bucket size
        if not l2size:
            l2size = level2.groupby('datetime')['price'].agg(np.ptp).reset_index()['price'].median()
        # 10 ask steps + 10 bid steps
        buckets = 20
        bucketsize = l2size / buckets

        # If price is too out, set maximum possible bucket
        level2['bucket'] = (level2['price'] - level2['price_middle']) // bucketsize
        maxbucket = buckets // 2 - 1
        minbucket = -buckets // 2
        level2['bucket'][level2['bucket'] > maxbucket] = maxbucket
        level2['bucket'][level2['bucket'] < minbucket] = minbucket

        # Calculate volume inside each group
        askgroups = level2[level2['bucket'] >= 0].groupby(['datetime', 'bucket'])['ask_vol'].sum().reset_index(level=1)
        askgroups['bucket'] = askgroups['bucket'].astype(int)
        askfeatures = askgroups.reset_index().pivot_table(index='datetime', columns='bucket', values='ask_vol')
        # Add absent buckets (rare case)
        for col in range(0, maxbucket + 1):
            if col not in askfeatures.columns:
                askfeatures[col] = 0
        askfeatures = askfeatures[sorted(askfeatures)]
        askfeatures.columns = ['l2_bucket_' + str(col) for col in askfeatures.columns]

        bidgroups = level2[level2['bucket'] < 0].groupby(['datetime', 'bucket'])['bid_vol'].sum().reset_index(level=1)
        bidgroups['bucket'] = bidgroups['bucket'].astype(int)
        bidfeatures = bidgroups.reset_index().pivot_table(index='datetime', columns='bucket', values='bid_vol')
        # Add absent buckets (rare case)
        for col in range(minbucket, 0):
            if col not in bidfeatures.columns:
                bidfeatures[col] = 0
        bidfeatures = bidfeatures[sorted(bidfeatures)]
        bidfeatures.columns = ['l2_bucket_' + str(col) for col in bidfeatures.columns]

        # Ask + bid buckets
        level2features = bidfeatures.merge(askfeatures, on='datetime')
        return level2features
