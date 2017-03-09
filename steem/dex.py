import random

from .instance import shared_steem_instance
from pistonbase import transactions

from .storage import configStorage as config


class Dex(object):
    """ This class allows to access calls specific for the internal
        exchange of STEEM.

        :param Steem steem_instance: Steem() instance to use when accesing a RPC

    """
    steem = None
    assets = ["STEEM", "SBD"]

    def __init__(self, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        # ensure market_history is registered
        self.steem.rpc.apis = list(set(self.steem.rpc.apis + ["market_history"]))
        self.steem.rpc.register_apis()

    def _get_asset(self, symbol):
        """ Return the properties of the assets tradeable on the
            network.

            :param str symbol: Symbol to get the data for (i.e. STEEM, SBD, VESTS)
        """
        if symbol == "STEEM":
            return {"symbol": "STEEM",
                    "precision": 3
                    }
        elif symbol == "SBD":
            return {"symbol": "SBD",
                    "precision": 3
                    }
        elif symbol == "VESTS":
            return {"symbol": "VESTS",
                    "precision": 6
                    }
        else:
            return None

    def _get_assets(self, quote):
        """ Given the `quote` asset, return base. If quote is SBD, then
            base is STEEM and vice versa.
        """
        assets = self.assets.copy()
        assets.remove(quote)
        base = assets[0]
        return self._get_asset(quote), self._get_asset(base)

    def returnTicker(self):
        """ Returns the ticker for all markets.

            Output Parameters:

            * ``latest``: Price of the order last filled
            * ``lowest_ask``: Price of the lowest ask
            * ``highest_bid``: Price of the highest bid
            * ``sbd_volume``: Volume of SBD
            * ``steem_volume``: Volume of STEEM
            * ``percent_change``: 24h change percentage (in %)

            .. note::

                Market is STEEM:SBD and prices are SBD per STEEM!

            Sample Output:

            .. code-block:: js

                 {'highest_bid': 0.30100226633322913,
                  'latest': 0.0,
                  'lowest_ask': 0.3249636958897082,
                  'percent_change': 0.0,
                  'sbd_volume': 108329611.0,
                  'steem_volume': 355094043.0}


        """
        ticker = {}
        t = self.steem.rpc.get_ticker(api="market_history")
        ticker = {'highest_bid': float(t['highest_bid']),
                  'latest': float(t["latest"]),
                  'lowest_ask': float(t["lowest_ask"]),
                  'percent_change': float(t["percent_change"]),
                  'sbd_volume': t["sbd_volume"],
                  'steem_volume': t["steem_volume"]}
        return ticker

    def return24Volume(self):
        """ Returns the 24-hour volume for all markets, plus totals for primary currencies.

            Sample output:

            .. code-block:: js

                {'sbd_volume': 108329.611, 'steem_volume': 355094.043}

        """
        v = self.steem.rpc.get_volume(api="market_history")
        return {'sbd_volume': v["sbd_volume"],
                'steem_volume': v["steem_volume"]}

    def returnOrderBook(self, limit=25):
        """ Returns the order book for the SBD/STEEM markets in both orientations.

            :param int limit: Limit the amount of orders (default: 25)

            .. note::

                Market is STEEM:SBD and prices are SBD per STEEM!

            Sample output:

            .. code-block:: js

                {'asks': [{'price': 3.086436224481787,
                           'sbd': 318547,
                           'steem': 983175},
                          {'price': 3.086429621198315,
                           'sbd': 2814903,
                           'steem': 8688000}],
                 'bids': [{'price': 3.0864376216446257,
                           'sbd': 545133,
                           'steem': 1682519},
                          {'price': 3.086440512632327,
                           'sbd': 333902,
                           'steem': 1030568}]},
        """
        orders = self.steem.rpc.get_order_book(limit, api="market_history")
        r = {"asks": [], "bids": []}
        for side in ["bids", "asks"]:
            for o in orders[side]:
                r[side].append({
                    'price': float(o["price"]),
                    'sbd': o["sbd"] / 10 ** 3,
                    'steem': o["steem"] / 10 ** 3,
                })
        return r

    def returnBalances(self, account=None):
        """ Return SBD and STEEM balance of the account

            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        return self.steem.get_balances(account)

    def returnOpenOrders(self, account=None):
        """ Return open Orders of the account

            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        orders = self.steem.rpc.get_open_orders(account, limit=1000)
        return orders

    def returnTradeHistory(self, time=1 * 60 * 60, limit=100):
        """ Returns the trade history for the internal market

            :param int hours: Show the last x seconds of trades (default 1h)
            :param int limit: amount of trades to show (<100) (default: 100)
        """
        assert limit <= 100, "'limit' has to be smaller than 100"
        return self.steem.rpc.get_trade_history(
            transactions.formatTimeFromNow(-time),
            transactions.formatTimeFromNow(),
            limit,
            api="market_history"
        )

    def returnMarketHistoryBuckets(self):
        return self.steem.rpc.get_market_history_buckets(api="market_history")

    def returnMarketHistory(
        self,
        bucket_seconds=60 * 5,
        start_age=1 * 60 * 60,
        stop_age=0,
    ):
        """ Return the market history (filled orders).

            :param int bucket_seconds: Bucket size in seconds (see `returnMarketHistoryBuckets()`)
            :param int start_age: Age (in seconds) of the start of the window (default: 1h/3600)
            :param int end_age: Age (in seconds) of the end of the window (default: now/0)

            Example:

            .. code-block:: js

                 {'close_sbd': 2493387,
                  'close_steem': 7743431,
                  'high_sbd': 1943872,
                  'high_steem': 5999610,
                  'id': '7.1.5252',
                  'low_sbd': 534928,
                  'low_steem': 1661266,
                  'open': '2016-07-08T11:25:00',
                  'open_sbd': 534928,
                  'open_steem': 1661266,
                  'sbd_volume': 9714435,
                  'seconds': 300,
                  'steem_volume': 30088443},
        """
        return self.steem.rpc.get_market_history(
            bucket_seconds,
            transactions.formatTimeFromNow(-start_age - stop_age),
            transactions.formatTimeFromNow(-stop_age),
            api="market_history"
        )

    def buy(self,
            amount,
            quote_symbol,
            rate,
            expiration=7 * 24 * 60 * 60,
            killfill=False,
            account=None,
            orderid=None):
        """ Places a buy order in a given market (buy ``quote``, sell
            ``base`` in market ``quote_base``). If successful, the
            method will return the order creating (signed) transaction.

            :param number amount: Amount of ``quote`` to buy
            :param str quote_symbol: STEEM, or SBD
            :param float price: price denoted in ``base``/``quote``
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)
            :param str account: (optional) the source account for the transfer if not ``default_account``
            :param int orderid: (optional) a 32bit orderid for tracking of the created order (random by default)

            Prices/Rates are denoted in 'base', i.e. the STEEM:SBD market
            is priced in SBD per STEEM.
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        # We buy quote and pay with base
        quote, base = self._get_assets(quote=quote_symbol)
        op = transactions.Limit_order_create(**{
            "owner": account,
            "orderid": orderid or random.getrandbits(32),
            "amount_to_sell": '{:.{prec}f} {asset}'.format(
                amount * rate,
                prec=base["precision"],
                asset=base["symbol"]),
            "min_to_receive": '{:.{prec}f} {asset}'.format(
                amount,
                prec=quote["precision"],
                asset=quote["symbol"]),
            "fill_or_kill": killfill,
            "expiration": transactions.formatTimeFromNow(expiration)
        })
        return self.steem.finalizeOp(op, account, "active")

    def sell(self,
             amount,
             quote_symbol,
             rate,
             expiration=7 * 24 * 60 * 60,
             killfill=False,
             account=None,
             orderid=None):
        """ Places a sell order in a given market (sell ``quote``, buy
            ``base`` in market ``quote_base``). If successful, the
            method will return the order creating (signed) transaction.

            :param number amount: Amount of ``quote`` to sell
            :param str quote_symbol: STEEM, or SBD
            :param float price: price denoted in ``base``/``quote``
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)
            :param str account: (optional) the source account for the transfer if not ``default_account``
            :param int orderid: (optional) a 32bit orderid for tracking of the created order (random by default)

            Prices/Rates are denoted in 'base', i.e. the STEEM:SBD market
            is priced in SBD per STEEM.
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        # We buy quote and pay with base
        quote, base = self._get_assets(quote=quote_symbol)
        op = transactions.Limit_order_create(**{
            "owner": account,
            "orderid": orderid or random.getrandbits(32),
            "amount_to_sell": '{:.{prec}f} {asset}'.format(
                amount,
                prec=quote["precision"],
                asset=quote["symbol"]),
            "min_to_receive": '{:.{prec}f} {asset}'.format(
                amount * rate,
                prec=base["precision"],
                asset=base["symbol"]),
            "fill_or_kill": killfill,
            "expiration": transactions.formatTimeFromNow(expiration)
        })
        return self.steem.finalizeOp(op, account, "active")

    def cancel(self, orderid, account=None):
        """ Cancels an order you have placed in a given market.

            :param int orderid: the 32bit orderid
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = transactions.Limit_order_cancel(**{
            "owner": account,
            "orderid": orderid,
        })
        return self.steem.finalizeOp(op, account, "active")

    def get_lowest_ask(self):
        """ Return the lowest ask.

            .. note::

                Market is STEEM:SBD and prices are SBD per STEEM!

            Example:

            .. code-block:: js

                 {'price': '0.32399833185738391',
                   'sbd': 320863,
                   'steem': 990323}
        """
        orders = self.returnOrderBook(1)
        return orders["asks"][0]

    def get_higest_bid(self):
        """ Return the highest bid.

            .. note::

                Market is STEEM:SBD and prices are SBD per STEEM!

            Example:

            .. code-block:: js

                 {'price': '0.32399833185738391',
                  'sbd': 320863,
                  'steem': 990323}
        """
        orders = self.returnOrderBook(1)
        return orders["bids"][0]

    def transfer(self, *args, **kwargs):
        """ Dummy to redirect to steem.transfer()
        """
        return self.steem.transfer(*args, **kwargs)
