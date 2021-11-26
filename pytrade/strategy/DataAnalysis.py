import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

candles_path = "./../data/QJSIM_SBER_candles_2021-11-07.csv"
quotes_path = "./../data/QJSIM_SBER_quotes_2021-11-07.csv"
level2_path = "./../data/QJSIM_SBER_level2_2021-11-07.csv"

candles: pd.DataFrame = pd.read_csv(candles_path, parse_dates=True,
                                    names=['datetime', 'ticker', 'open', 'high', 'low', 'close', 'volume'],
                                    index_col=['datetime'])
candles = candles[~candles.index.duplicated(keep='first')].sort_index()

# Read quotes
quotes: pd.DataFrame = pd.read_csv(quotes_path, parse_dates=True,
                                   names=['datetime', 'ticker', 'bid', 'ask', 'last', 'last_change'],
                                   index_col=['datetime'])
quotes = quotes[~quotes.index.duplicated(keep='first')].sort_index()

# Read level2
level2 = pd.read_csv(level2_path, parse_dates=['datetime'], names=['datetime', 'ticker', 'price', 'bid_vol', 'ask_vol'])


# print(quotes['last_change'].unique())
# print(quotes.tail())
# Show quotes plot
# print(level2.tail)
# level2['vol'] = level2['bid_vol'].fillna(0) + level2['ask_vol'].fillna(0)
# level2 = level2.drop(columns=['bid_vol', 'ask_vol']).set_index('datetime')


def preprocess(df: pd.DataFrame):
    # Pivot to create feature columns of level2 prices and volumes

    df["num"] = df.groupby("datetime").cumcount() + 1
    price_pivoted = df.pivot(index="datetime", columns="num", values="price")
    price_pivoted.columns = "price" + price_pivoted.columns.astype(str)
    price_pivoted["base"] = (price_pivoted["price10"] + price_pivoted["price11"]) / 2
    for n in range(1, len([c for c in price_pivoted.columns if c.startswith("price")]) + 1):
        col = "price" + str(n)
        price_pivoted[col] = price_pivoted[col] - price_pivoted["base"]

    bid_vol_pivoted = df.pivot(index="datetime", columns="num", values="bid_vol")
    bid_vol_pivoted.columns = "bid_vol" + bid_vol_pivoted.columns.astype(str)

    ask_vol_pivoted = df.pivot(index="datetime", columns="num", values="ask_vol")
    ask_vol_pivoted.columns = "as_vol" + ask_vol_pivoted.columns.astype(str)

    pivoted = price_pivoted.join(bid_vol_pivoted).join(ask_vol_pivoted)
    p = Pipeline()
    return pivoted
    # Form level2

    # Reverse, rolling and reverse back to calc future max and min
    # Add future min/max
    # predict_window = "2min"
    # self.quotes["nextmax"] = self.quotes["ask"][::-1].rolling(predict_window).max()[::-1]
    # self.quotes["nextmin"] = self.quotes["ask"][::-1].rolling(predict_window).min()[::-1]
    #
    # # Add last closest
    # m = pd.merge_asof(self.quotes, self.candles, left_index=True, right_index=True, tolerance=pd.Timedelta("1 min"))
    # print(m.head(10))


def level2_features(level2: pd.DataFrame):
    # Calc middle price between ask and bid
    level2 = level2.set_index("datetime")
    askmin = level2[level2['ask_vol'].notna()].groupby('datetime')['price'].min().reset_index().set_index("datetime")
    level2['price_min'] = askmin['price']
    bidmax = level2[level2['bid_vol'].notna()].groupby('datetime')['price'].max().reset_index().set_index("datetime")
    level2['price_max'] = bidmax['price']
    level2['price_middle'] = (askmin['price'] + bidmax['price']) / 2

    # Assign a group to each level2 item
    # scalar level2 size and bucket size
    l2size = level2.groupby('datetime')['price'].agg(np.ptp).reset_index()['price'].median()
    # 10 ask steps + 10 bid steps
    buckets = 20
    bucketsize = l2size / buckets

    level2['bucket'] = (level2['price'] - level2['price_middle']) // bucketsize
    level2['bucket'][level2['bucket'] >= (buckets // 2)] = buckets // 2-1
    level2['bucket'][level2['bucket'] < -buckets // 2] = -buckets // 2
    m=level2['bucket'].max()

    # Calculate volume inside each group
    askgroups = level2[level2['bucket'] >= 0].groupby(['datetime', 'bucket'])['ask_vol'].sum().reset_index(level=1)
    askgroups['bucket'] = askgroups['bucket'].astype(int)
    bidgroups = level2[level2['bucket'] < 0].groupby(['datetime', 'bucket'])['bid_vol'].sum().reset_index(level=1)
    bidgroups['bucket'] = bidgroups['bucket'].astype(int)
    askfeatures = askgroups.reset_index().pivot_table(index='datetime', columns='bucket', values='ask_vol')
    askfeatures.columns = ['l2_bucket_' + str(col) for col in askfeatures.columns]
    bidfeatures = bidgroups.reset_index().pivot_table(index='datetime', columns='bucket', values='bid_vol')
    bidfeatures.columns = ['l2_bucket_' + str(col) for col in bidfeatures.columns]
    level2features=bidfeatures.merge(askfeatures,on='datetime')
    return level2_features


level2 = level2_features(level2)

with_min_max = level2.groupby('datetime').agg({'ask': 'min', 'bid': 'max'}).reset_index()
level2['price'] = with_min_max['ask_min'] - with_min_max['bid_max']

s = level2.groupby('datetime').size()
print(level2.groupby('datetime').size().max())
u = level2['price'].unique()

level2 = level2.tail(1000)
level2 = preprocess(level2)

fig = px.scatter(level2, x=level2.index, y='price', size='vol')
fig.show()

# q = quotes.reset_index()
# plt.scatter(x=q["datetime"], y=q['bid'])
# plt.show()
