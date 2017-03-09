import datetime
import json
import math
import time
from contextlib import suppress

from piston.instance import shared_steem_instance

from .amount import Amount
from .converter import Converter
from steembase.exceptions import AccountDoesNotExistsException
from steem.utils import parse_time


class Account(dict):
    """ This class allows to easily access Account data

        :param str account_name: Name of the account
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    def __init__(
        self,
        account_name,
        steem_instance=None,
        lazy=False,
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.cached = False
        self.name = account_name

        # caches
        self._converter = None

        if not lazy:
            self.refresh()

    def refresh(self):
        account = self.steem.rpc.get_account(self.name)
        if not account:
            raise AccountDoesNotExistsException
        super(Account, self).__init__(account)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Account, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return super(Account, self).items()

    @property
    def converter(self):
        if not self._converter:
            self._converter = Converter(self.steem)
        return self._converter

    @property
    def profile(self):
        with suppress(Exception):
            meta_str = self.get("json_metadata", "")
            return json.loads(meta_str).get('profile', dict())

    @property
    def sp(self):
        vests = Amount(self['vesting_shares']).amount
        return round(self.converter.vests_to_sp(vests), 3)

    @property
    def rep(self):
        return self.reputation()

    @property
    def balances(self):
        return self.get_balances()

    def get_balances(self, as_float=False):
        my_account_balances = self.steem.get_balances(self.name)
        balance = {
            "STEEM": my_account_balances["balance"],
            "SBD": my_account_balances["sbd_balance"],
            "VESTS": my_account_balances["vesting_shares"],
            "SAVINGS_STEEM": my_account_balances["savings_balance"],
            "SAVINGS_SBD": my_account_balances["savings_sbd_balance"]
        }
        if as_float:
            return {k: v.amount for k, v in balance.items()}
        else:
            return balance

    def reputation(self, precision=2):
        rep = int(self['reputation'])
        if rep == 0:
            return 25
        score = (math.log10(abs(rep)) - 9) * 9 + 25
        if rep < 0:
            score = 50 - score
        return round(score, precision)

    def voting_power(self):
        return self['voting_power'] / 100

    def get_followers(self):
        return [x['follower'] for x in self._get_followers(direction="follower")]

    def get_following(self):
        return [x['following'] for x in self._get_followers(direction="following")]

    def _get_followers(self, direction="follower", last_user=""):
        if direction == "follower":
            followers = self.steem.rpc.get_followers(self.name, last_user, "blog", 100, api="follow")
        elif direction == "following":
            followers = self.steem.rpc.get_following(self.name, last_user, "blog", 100, api="follow")
        if len(followers) >= 100:
            followers += self._get_followers(direction=direction, last_user=followers[-1][direction])[1:]
        return followers

    def has_voted(self, post):
        active_votes = {v["voter"]: v for v in getattr(post, "active_votes")}
        return self.name in active_votes

    def curation_stats(self):
        trailing_24hr_t = time.time() - datetime.timedelta(hours=24).total_seconds()
        trailing_7d_t = time.time() - datetime.timedelta(days=7).total_seconds()

        reward_24h = 0.0
        reward_7d = 0.0

        for reward in self.history2(filter_by="curation_reward", take=10000):

            timestamp = parse_time(reward['timestamp']).timestamp()
            if timestamp > trailing_7d_t:
                reward_7d += Amount(reward['reward']).amount

            if timestamp > trailing_24hr_t:
                reward_24h += Amount(reward['reward']).amount

        reward_7d = self.converter.vests_to_sp(reward_7d)
        reward_24h = self.converter.vests_to_sp(reward_24h)
        return {
            "24hr": reward_24h,
            "7d": reward_7d,
            "avg": reward_7d / 7,
        }

    def virtual_op_count(self):
        try:
            last_item = self.steem.rpc.get_account_history(self.name, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def get_account_votes(self):
        return self.steem.rpc.get_account_votes(self.name)

    def get_withdraw_routes(self):
        return self.steem.rpc.get_withdraw_routes(self.name, 'all')

    def get_conversion_requests(self):
        return self.steem.rpc.get_conversion_requests(self.name)

    @staticmethod
    def filter_by_date(items, start_time, end_time=None):
        start_time = parse_time(start_time).timestamp()
        if end_time:
            end_time = parse_time(end_time).timestamp()
        else:
            end_time = time.time()

        filtered_items = []
        for item in items:
            if 'time' in item:
                item_time = item['time']
            elif 'timestamp' in item:
                item_time = item['timestamp']
            timestamp = parse_time(item_time).timestamp()
            if end_time > timestamp > start_time:
                filtered_items.append(item)

        return filtered_items

    def export(self, load_extras=True):
        """ This method returns a dictionary that is type-safe to store as JSON or in a database.

            :param bool load_extras: Fetch extra information related to the account (this might take a while).
        """
        self.refresh()

        extras = dict()
        if load_extras:
            followers = self.get_followers()
            following = self.get_following()
            extras = {
                "followers": followers,
                "followers_count": len(followers),
                "following": following,
                "following_count": len(following),
                "curation_stats": self.curation_stats(),
                "withdrawal_routes": self.get_withdraw_routes(),
                "conversion_requests": self.get_conversion_requests(),
            }

        return {
            **self,
            **extras,
            "profile": self.profile,
            "sp": self.sp,
            "rep": self.rep,
            "balances": self.get_balances(as_float=True),
        }

    def history(self, filter_by=None, start=0):
        """
        Take all elements from start to last from history, oldest first.
        """
        batch_size = 1000
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while True:
            if i == start_index:
                limit = batch_size
            else:
                limit = batch_size - 1
            history = self.steem.rpc.get_account_history(self.name, i, limit)
            for item in history:
                index = item[0]
                if index >= max_index:
                    return

                op_type = item[1]['op'][0]
                op = item[1]['op'][1]
                timestamp = item[1]['timestamp']
                trx_id = item[1]['trx_id']

                def construct_op(account_name):
                    r = {
                        "index": index,
                        "account": account_name,
                        "trx_id": trx_id,
                        "timestamp": timestamp,
                        "type": op_type,
                    }
                    r.update(op)
                    return r

                if filter_by is None:
                    yield construct_op(self.name)
                else:
                    if type(filter_by) is list:
                        if op_type in filter_by:
                            yield construct_op(self.name)

                    if type(filter_by) is str:
                        if op_type == filter_by:
                            yield construct_op(self.name)
            i += batch_size

    def history2(self, filter_by=None, take=1000):
        """
        Take X elements from most recent history, oldest first.
        """
        max_index = self.virtual_op_count()
        start_index = max_index - take
        if start_index < 0:
            start_index = 0

        return self.history(filter_by, start=start_index)

    def rawhistory(
        self, first=99999999999,
        limit=-1, only_ops=[], exclude_ops=[]
    ):
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param str account: account name to get history for
            :param int first: sequence number of the first transaction to return
            :param int limit: limit number of transactions to return
            :param array only_ops: Limit generator by these operations
        """
        cnt = 0
        _limit = 100
        if _limit > first:
            _limit = first
        while first > 0:
            # RPC call
            txs = self.steem.rpc.get_account_history(self.name, first, _limit)
            for i in txs[::-1]:
                if exclude_ops and i[1]["op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1]["op"][0] in only_ops:
                    cnt += 1
                    yield i
                    if limit >= 0 and cnt >= limit:
                        break
            if limit >= 0 and cnt >= limit:
                break
            if len(txs) < _limit:
                break
            first = txs[0][0] - 1  # new first
            if _limit > first:
                _limit = first
