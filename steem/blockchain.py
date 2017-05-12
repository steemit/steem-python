import hashlib
import json
import time
import warnings
from typing import Union

from .instance import shared_steemd_instance
from .utils import parse_time


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
        return self.steem.get_block(self.get_current_block_num())

    def stream_from(self, start_block=None, end_block=None, batch_operations=False, full_blocks=False, **kwargs):
        """ This call yields raw blocks or operations depending on ``full_blocks`` param.
        
        By default, this generator will yield operations, one by one.
        You can choose to yield lists of operations, batched to contain 
        all operations for each block with ``batch_operations=True``.
        You can also yield full blocks instead, with ``full_blocks=True``.
        
        Args:
            start_block (int): Block to start with. If not provided, current (head) block is used.
            end_block (int): Stop iterating at this block. If not provided, this generator will run forever (streaming mode).
            batch_operations (bool): (Defaults to False) Rather than yielding operations one by one, 
                yield a list of all operations for each block.
            full_blocks (bool): (Defaults to False) Rather than yielding operations, return raw, unedited blocks as 
                provided by steemd. This mode will NOT include virtual operations.
        """

        _ = kwargs  # we need this
        # Let's find out how often blocks are generated!
        block_interval = self.config().get("STEEMIT_BLOCK_INTERVAL")

        if not start_block:
            start_block = self.get_current_block_num()

        while True:
            head_block = self.get_current_block_num()

            for block_num in range(start_block, head_block + 1):
                if end_block and block_num > end_block:
                    raise StopIteration("Reached stop block at: #%s" % end_block)

                if full_blocks:
                    yield self.steem.get_block(block_num)
                elif batch_operations:
                    yield self.steem.get_ops_in_block(block_num, False)
                else:
                    yield from self.steem.get_ops_in_block(block_num, False)

            # next round
            start_block = head_block + 1
            time.sleep(block_interval)

    def stream(self, filter_by: Union[str, list] = list(), *args, **kwargs):
        """ Yield a stream of operations, starting with current head block.

            Args:
                filter_by (str, list): List of operations to filter for
        """
        if isinstance(filter_by, str):
            filter_by = [filter_by]

        for ops in self.stream_from(*args, **kwargs):

            # deal with different self.stream_from() outputs
            events = ops
            if type(ops) == dict:
                if 'witness_signature' in ops:
                    raise ValueError('Blockchain.stream() is for operation level streams. '
                                     'For block level streaming, use Blockchain.stream_from()')
                events = [ops]

            for event in events:
                op_type, op = event['op']
                if not filter_by or op_type in filter_by:
                    # return unmodified steemd output
                    if kwargs.get('raw_output'):
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
        """ Yield a stream of historic operations.
        
        Similar to ``Blockchain.stream()``, but starts at beginning of chain unless ``start_block`` is set.
        
        Args:
            filter_by (str, list): List of operations to filter for
            start_block (int): Block to start with. If not provided, start of blockchain is used (block 1).
            end_block (int): Stop iterating at this block. If not provided, this generator will run forever.
            raw_output (bool): (Defaults to False). If True, return ops in a unmodified steemd structure.
        """
        return self.stream(
            filter_by=filter_by,
            start_block=start_block,
            end_block=end_block,
            raw_output=raw_output,
            **kwargs
        )

    def ops(self, *args, **kwargs):
        raise DeprecationWarning('Blockchain.ops() is deprecated. Please use Blockchain.stream_from() instead.')

    def replay(self, **kwargs):
        warnings.warn('Blockchain.replay() is deprecated. Please use Blockchain.history() instead.')
        return self.history(**kwargs)

    @staticmethod
    def hash_op(event: dict):
        """ This method generates a hash of blockchain operation. """
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(bytes(data, 'utf-8')).hexdigest()

    def get_all_usernames(self, *args, **kwargs):
        """ Fetch the full list of STEEM usernames. """
        _ = args, kwargs
        warnings.warn('Blockchain.get_all_usernames() is now at Steemd.get_all_usernames().')
        return self.steem.get_all_usernames()
