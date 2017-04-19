import hashlib
import json
import re
import time
import warnings
from typing import Union

from funcy.colls import walk_values

from .amount import Amount
from .block import Block
from .instance import shared_steemd_instance
from .utils import parse_time, keep_in_dict


class Blockchain(object):
    """ Access the blockchain and read data from it.

    Args:
        steemd_instance (Steemd): Steemd() instance to use when accessing a RPC
        mode (str): `irreversible` or `head`. `irreversible` is default.
    """

    def __init__(self, steemd_instance=None, mode="irreversible"):
        self.steem = steemd_instance or shared_steemd_instance()

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

    def ops(self, start=None, stop=None, full_blocks=False, only_virtual_ops=False, **kwargs):
        """
        Yields all operations (including virtual operations) starting from ``start``.
        This call returns a generator with blocks or operations depending on full_blocks param.

            :param bool full_blocks: If true, will return a list of all operations in block
             rather than yielding each operation separately.
            :param int start: Starting block
            :param int stop: Stop at this block
            :param bool only_virtual_ops: Only yield virtual operations
        """

        _ = kwargs  # we need this
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

    def stream(self, filter_by: Union[str, list] = list(), *args, **kwargs):
        """ Yield a stream of blocks

            Args:
                filter_by (str, list): List of operations to filter for
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
                    raw_output = kwargs.get('raw_output')
                    if raw_output:
                        yield event
                    else:
                        yield {
                            **op,
                            "_id": self.hash_op(event),
                            "type": op_type,
                            "timestamp": parse_time(event.get("timestamp")),
                            "block_num": event.get("block"),
                            "trx_id": event.get("trx_id"),
                        }

    def history(self, filter_by: Union[str, list] = list(), start_block=1, end_block=None, raw_output=False, **kwargs):
        """ Similar to Blockchain.stream, but with explicit arguments for start and end blocks. """
        return self.stream(
            filter_by=filter_by,
            start=start_block,
            stop=end_block,
            raw_output=raw_output,
            **kwargs
        )

    def replay(self, **kwargs):
        warnings.warn('Blockchain.replay() is deprecated. Please use Blockchain.history() instead.')
        return self.history(**kwargs)

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
            return keep_in_dict(dict(Amount(value)), ['amount', 'asset'])

        if re.match('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', value):
            return parse_time(value)

    return value
