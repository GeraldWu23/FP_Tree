import pandas as pd
from pandas import Series, DataFrame
import pickle
from tqdm import tqdm
from collections import Counter


df = pd.read_csv('Groceries_dataset.csv')
for i, line in tqdm(df.iterrows()):
    df.at[i, 'itemDescription'] = df.at[i, 'itemDescription'] + ' '

series = df.groupby(by='Member_number').sum().loc[:, 'itemDescription']

for k, v in tqdm(series.items()):
    series[k] = list(set(v.split()))

obj = list()
counter = Counter()
for li in series.tolist():
    obj.extend(li)
    counter.update(li)

obj = list(set(obj))
obj = sorted(obj, key=lambda k: counter[k], reverse=True)  # sorted according to the count, from more to less

key2id = {}
id2key = {}
id = 0

for item in tqdm(obj):
    id2key[id] = item
    key2id[item] = id
    id += 1

dataset = []
for customer in tqdm(series.tolist()):
    dataset.append(sorted([key2id[item] for item in customer]))

with open('./data.pkl', 'wb') as datafile:
    pickle.dump(dataset, datafile)