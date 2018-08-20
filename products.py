# -*- coding: utf-8 -*-
"""
Created on Sat Aug  4 23:09:48 2018

@author: Julius
"""
import requests
import datetime as dt
import pandas as pd
import numpy as np
import time

url = 'https://api.pro.coinbase.com'

def get_products():
    r = requests.get(url + '/products')
    return r.json()

def get_product_ids(product_data):
    ids = []
    for i in product_data:
        ids.append(i['id'])
    return ids

def get_product_ticker(product_id):
    r = requests.get(url + '/products/' + product_id + '/ticker')
    return r.json()

def remove_irrelevent(product_ids):
    new_ids = []
    for i in product_ids:
        if not ('EUR' in i or 'GBP' in i):
            new_ids.append(i)
    return new_ids

def get_relevent_ids():
    product_data = get_products()
    ids = get_product_ids(product_data)
    return remove_irrelevent(ids)

def get_historic_rates(product_id, start=None, end=None, granularity = None):
    #/products/<product-id>/candles
    #print(end)
    #print(start)
    if granularity != None:
        assert granularity in [60, 300, 900, 3600, 21600, 86400]
    r = requests.get(url + '/products/'+product_id+'/candles', params = {'start': start, 'end': end, 'granularity': granularity})
    return r.text
    
def seconds_to_iso(seconds):
    date = dt.datetime.utcfromtimestamp(seconds).isoformat()
    return date

def get_long_historic_rates(product_id):
    # Oldest date: 2014-12-01
    limit = 300
    iterations = 7
    delta = dt.timedelta(days = limit)
    now = dt.datetime.now()
    temp = now
    
    
    columns = ['time', 'low', 'high', 'open', 'close', 'volume']
    
    data = []
    for i in range(iterations):
        start = (temp - delta).isoformat()
        end = temp.isoformat()
        text = get_historic_rates(product_id, start=start, end=end, granularity=86400)
        try:
            df = pd.read_json(text)
        except:
            print(text)
            break
        data.append(df)
        temp -= delta
        time.sleep(1)
    price_data = pd.concat(data, axis=0, ignore_index=True)
    price_data = price_data.rename(columns={key:value for key,value in enumerate(columns)})
    price_data['date'] = price_data['time']
    price_data['date'] = price_data['date'].apply(seconds_to_iso)
    price_data = price_data.set_index('date')
    return price_data

def get_hourly_historic_rates(product_id):
    beginning = dt.datetime(2014,12,1)
    limit = 300
    now = dt.datetime.now()
    temp = now
    delta = dt.timedelta(hours = limit)
    data = []
    test = False
    while temp > beginning:
        start = (temp - delta).isoformat()
        end = temp.isoformat()
        text = get_historic_rates(product_id, start=start, end=end, granularity=3600)
        try:
            df = pd.read_json(text)
        except:
            print(text)
            break
        
        if df.empty:
            if test:
                break
            test = True
        else:
            test = False
        print(df)
        data.append(df)
        temp -= delta
        time.sleep(1)
    price_data = pd.concat(data, axis=0, ignore_index=True)
    columns = ['time', 'low', 'high', 'open', 'close', 'volume']
    price_data = price_data.rename(columns={key:value for key,value in enumerate(columns)})
    price_data['date'] = price_data['time']
    price_data['date'] = price_data['date'].apply(seconds_to_iso)
    price_data = price_data.set_index('date')
    price_data.index = pd.to_datetime(price_data.index)
    return price_data
    
def read_hourly(product_id):
    try:
        price_data = pd.read_csv(product_id + '.csv')
        price_data = price_data.set_index('date')
    except:
        price_data = get_hourly_historic_rates(product_id)
        price_data.to_csv(product_id + '.csv')
    price_data.index = pd.to_datetime(price_data.index)
    return price_data

def update_hourly(product_id):
    price_data = read_hourly(product_id)
    most_recent = price_data.index[0]
    start = (most_recent + dt.timedelta(hours = 1)).isoformat()
    text = get_historic_rates(product_id, start=start, end=dt.datetime.now().isoformat(), granularity=3600)
    data = pd.read_json(text)
    if not data.empty:
        columns = ['time', 'low', 'high', 'open', 'close', 'volume']
        data = data.rename(columns={key:value for key,value in enumerate(columns)})
        data['date'] = data['time']
        data['date'] = data['date'].apply(seconds_to_iso)
        data = data.set_index('date')
        data.index = pd.to_datetime(data.index)
        price_data = pd.concat([data, price_data], axis=0, sort = False)
        price_data.to_csv(product_id + '.csv')
        print('\nUpdater: added rows')
        print(data)
    return price_data

def normalize(df):
    #data['pct_change'] = data['close'].pct_change()
    df['log_diff'] = df['close'].rolling(window=2).apply(lambda x: np.log(x[0]) - np.log(x[1]), raw=True)
    df['pct_change'] = df['close'].rolling(window=2).apply(lambda x: (x[0] - x[1])/x[0], raw=True)
    df['hour_change'] = df['close'].rolling(window=2).apply(lambda x: (x[0] - np.min(x))/(np.max(x)-np.min(x)), raw=True)
    df['day_change'] = df['close'].rolling(window=24).apply(lambda x: (x[0] - np.min(x))/(np.max(x)-np.min(x)), raw=True)
    df['week_change'] = df['close'].rolling(window=24*7).apply(lambda x: (x[0] - np.min(x))/(np.max(x)-np.min(x)), raw=True)
    df['month_change'] = df['close'].rolling(window=24*7*30).apply(lambda x: (x[0] - np.min(x))/(np.max(x)-np.min(x)), raw=True)
    # more ideas: z scores over n timesteps
    return df

if __name__ == '__main__':
    ids = get_relevent_ids()
    for i in ids:
        print(i)
    #data = update_hourly(ids[0])
    #normalize(data)
    df = update_hourly(ids[0])
    df = normalize(df)

#for just date: datetime.date.isoformat(datetime.datetime.now())

#h = get_historic_rates(ids[2], start=start, end=end, granularity=86400)
#print(h)
#df = pandas.read_json(h)

#df = df.rename(index=str, columns={key:value for key,value in enumerate(['time', 'low', 'high', 'open', 'close', 'volume'])})
#df['time'] = df['time'].apply(seconds_to_iso)
#print(df)

#price_data = get_hourly_historic_rates(ids[0])
#price_data.to_csv('bitcoin_data.csv')

#print(price_data)


