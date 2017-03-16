import hashlib
import json
import re
import time
from typing import Union

from funcy.colls import walk_values

from .amount import Amount
from .block import Block
from .instance import shared_steemd_instance
from .utils import parse_time, keep_in_dict


class Blockchain(object):
    """ Access the blockchain and read data from it.

    Args:
        steem_instance (Steemd): Steemd() instance to use when accessing a RPC
        mode (str): `irreversible` or `head`. `irreversible` is default.
    """
    def __init__(self, steem_instance=None, mode="irreversible"):
        self.steem = steem_instance or shared_steemd_instance()

        if mode == "irreversible":
            self.mode = 'last_irreversible_block_num'
        elif mode == "head":
            self.mode = "head_block_number"
        else:
            raise ValueError("invalid value for 'mode'!")

    def info(self):
        """ This call returns the *dynamic global properties*
        """
        return self.steem.get_dynamic_global_properties()

    def config(self):
        return self.steem.get_config()

    def get_current_block_num(self):
        """ This call returns the current block
        """
        return self.info().get(self.mode)

    def get_current_block(self):
        """ This call returns the current block
        """
        return Block(self.get_current_block_num())

    def ops(self, start=None, stop=None, full_blocks=False, only_virtual_ops=False):
        """
        Yields all operations (including virtual operations) starting from ``start``.
        This call returns a generator with blocks or operations depending on full_blocks param.

            :param bool full_blocks: If true, will return a list of all operations in block
             rather than yielding each operation separately.
            :param int start: Starting block
            :param int stop: Stop at this block
            :param bool only_virtual_ops: Only yield virtual operations
        """

        # Let's find out how often blocks are generated!
        block_interval = self.config().get("STEEMIT_BLOCK_INTERVAL")

        if not start:
            start = self.get_current_block_num()

        while True:
            head_block = self.get_current_block_num()

            for block_num in range(start, head_block + 1):
                if stop and block_num > stop:
                    raise StopIteration("Reached stop block at: #%s" % stop)

                if full_blocks:
                    yield self.steem.get_ops_in_block(block_num, only_virtual_ops)
                else:
                    yield from self.steem.get_ops_in_block(block_num, only_virtual_ops)

            # next round
            start = head_block + 1
            time.sleep(block_interval)

    def stream(self, filter_by=list(), *args, **kwargs):
        """ Yield a stream of blocks

            :param list filter_by: List of operations to filter for, e.g.
                vote, comment, transfer, transfer_to_vesting,
                withdraw_vesting, limit_order_create, limit_order_cancel,
                feed_publish, convert, account_create, account_update,
                witness_update, account_witness_vote, account_witness_proxy,
                pow, custom, report_over_production, fill_convert_request,
                comment_reward, curate_reward, liquidity_reward, interest,
                fill_vesting_withdraw, fill_order,
        """
        if isinstance(filter_by, str):
            filter_by = [filter_by]

        for ops in self.ops(*args, **kwargs):

            # deal with full_blocks optionality
            events = ops
            if type(ops) == dict:
                events = [ops]

            for event in events:
                op_type, op = event['op']
                if not filter_by or op_type in filter_by:
                    yield {
                        "_id": self.hash_op(event),
                        **op,
                        "type": op_type,
                        "timestamp": parse_time(event.get("timestamp")),
                        "block_num": event.get("block"),
                        "trx_id": event.get("trx_id"),
                    }

    def replay(self, start_block=1, end_block=None, filter_by=list(), **kwargs):
        """ Same as ``stream`` with different prototype
        """
        return self.stream(
            filter_by=filter_by,
            start=start_block,
            stop=end_block,
            **kwargs
        )

    @staticmethod
    def hash_op(event: dict):
        """ This method generates a hash of blockchain operation. """
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(bytes(data, 'utf-8')).hexdigest()

    @staticmethod
    def block_time(block_num):
        """ Returns a datetime of the block with the given block number. """
        return Block(block_num).time()

    def get_all_usernames(self, last_user=''):
        usernames = self.steem.lookup_accounts(last_user, 1000)
        batch = []
        while len(batch) != 1:
            batch = self.steem.lookup_accounts(usernames[-1], 1000)
            usernames += batch[1:]

        return usernames


def typify(value: Union[dict, list, set, str]):
    """ Enhance block operation with native types.

    Typify takes a blockchain operation or dict/list/value,
    and then it parses and converts string types into native data types where appropriate.
    """
    if type(value) == dict:
        return walk_values(typify, value)

    if type(value) in [list, set]:
        return list(map(typify, value))

    if type(value) == str:
        if re.match('^\d+\.\d+ (STEEM|SBD|VESTS)$', value):
            return keep_in_dict(Amount(value).__dict__, ['amount', 'asset'])

        if re.match('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', value):
            return parse_time(value)

    return value


if __name__ == '__main__':
    b = Blockchain()
    print(len(list(b.stream(start=9563511, stop=9563511))))
    quit(0)
    for event in b.stream(start=9563511, full_blocks=True):
        if event['trx_id'] == '0000000000000000000000000000000000000000':
            print(event)
