import hashlib
import json
import time
import warnings

from .instance import shared_steemd_instance,stm
from .utils import parse_time

import logging
logger = logging.getLogger(__name__)

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
                    for ops in self.steem.get_ops_in_block(block_num, False):
                        yield ops

            # next round
            start_block = head_block + 1
            time.sleep(block_interval)


    def reliable_stream(self, start_block=None, block_interval=None, update_interval=False, batch_operations=False, full_blocks=False, timeout=None, **kwargs):
        """ A version of stream_from() intended for use in services that NEED reliable (nonstop) streaming

        By default, works same as stream_from() but will also keep trying until getting a response from steemd, allowing catching up after server downtime.

        Warnings:
            To ensure reliability, this method does some weird none-standard things with the steemd client

        Args:
            start_block (int): Block to start with. If not provided, current (head) block is used.
            block_interval (int): Time between block generations. If not provided, will attempt to query steemd for this value
            batch_operations (bool): (Defaults to False) Rather than yielding operations one by one, 
                yield a list of all operations for each block.
            full_blocks (bool): (Defaults to False) Rather than yielding operations, return raw, unedited blocks as 
                provided by steemd. This mode will NOT include virtual operations.
            timeout (int): Time to wait on response from steemd before assuming timeout and retrying queries. If not provided, this will default to block_interval/4
                for all queries except get_block_interval() - where it will default to 2 seconds for initial setup
        """
        def get_reliable_client(_timeout):
            # we want to fail fast and try the next node quickly
            return stm.steemd.Steemd(nodes=self.steem.nodes,retries=1,timeout=_timeout,re_raise=True)
        def reliable_query(_client,_method,_api,*_args):
            # this will ALWAYS eventually return, at all costs
            retval = None
            while retval is None:
               try:
                  retval = _client.call(_method,*_args,api=_api)
               except Exception as e:
                  logger.info('Failed to get response', extra=dict(exc=e,response=retval,api_name=_api,api_method=_method,api_args=_args))
                  retval = None
               if retval is None: time.sleep(1)
            return retval

        def get_reliable_block_interval(_client):
            return reliable_query(_client,'get_config','database_api').get('STEEMIT_BLOCK_INTERVAL')

        def get_reliable_current_block(_client):
            return reliable_query(_client,'get_dynamic_global_properties','database_api').get(self.mode)

        def get_reliable_blockdata(_client,_block_num):
            return reliable_query(_client,'get_block', 'database_api', block_num)

        def get_reliable_ops_in_block(_client,_block_num):
            return reliable_query(_client,'get_ops_in_block','database_api',block_num,False)

        if timeout is None:
           if block_interval is None:
              _reliable_client = get_reliable_client(2)
              block_interval   = get_reliable_block_interval(_reliable_client)
           else:
              timeout          = block_interval/4
              _reliable_client = get_reliable_client(timeout)
        else:
           _reliable_client = get_reliable_client(timeout)
        if block_interval is None:
           block_interval = get_reliable_block_interval(_reliable_client)
        if start_block is None:
           start_block = get_reliable_current_block(_reliable_client)

        while True:
           sleep_interval = block_interval/4
           head_block = get_reliable_current_block(_reliable_client)

           for block_num in range(start_block,head_block+1):
               if full_blocks:
                  yield get_reliable_current_block(_reliable_client,head_block)
               elif batch_operations:
                  yield get_reliable_ops_in_block(_reliable_client,head_block)
               else:
                  for reliable_ops in get_reliable_ops_in_block(_reliable_client,head_block):
                    yield reliable_ops
               sleep_interval = sleep_interval/2

           time.sleep(sleep_interval)
           start_block = head_block + 1


    def stream(self, filter_by = list(), *args, **kwargs):
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
                        yield op.update({
                            "_id": self.hash_op(event),
                            "type": op_type,
                            "timestamp": parse_time(event.get("timestamp")),
                            "block_num": event.get("block"),
                            "trx_id": event.get("trx_id"),
                        })

    def history(self, filter_by = list(), start_block=1, end_block=None, raw_output=False, **kwargs):
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
    def hash_op(event):
        """ This method generates a hash of blockchain operation. """
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(bytes(data, 'utf-8')).hexdigest()

    def get_all_usernames(self, *args, **kwargs):
        """ Fetch the full list of STEEM usernames. """
        _ = args, kwargs
        warnings.warn('Blockchain.get_all_usernames() is now at Steemd.get_all_usernames().')
        return self.steem.get_all_usernames()
