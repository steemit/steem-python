import json
import requests
import time
import datetime

def fetch_historic_steem_prices():
    cmurl = 'https://graphs2.coinmarketcap.com/' + \
            'currencies/steem'
    start_epoch = 1460996371
    now_epoch = time.time()
    fetch_url = "%s/%i/%i/" % (
        cmurl, start_epoch * 1000, now_epoch * 1000
    )
    usd_prices = requests.get(fetch_url).json()['price_usd']
    output = {}
    for pair in usd_prices:
        output[epochms_to_iso8601(pair[0])] = pair[1]
    return output

def epochms_to_iso8601(msts):
    return(
        datetime.datetime.fromtimestamp(
            int(msts/1000)
        ).strftime('%Y-%m-%d')
    )
