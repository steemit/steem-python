from piston.instance import shared_steem_instance

from steembase.exceptions import BlockDoesNotExistsException
from steem.utils import parse_time


class Block(dict):
    """ Read a single block from the chain

        :param int block: block number
        :param Steem steem_instance: Steem() instance to use when accesing a RPC
        :param bool lazy: Use lazy loading

    """
    def __init__(
        self,
        block,
        steem_instance=None,
        lazy=False
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.cached = False
        self.block = block

        if isinstance(block, Block):
            super(Block, self).__init__(block)
            self.cached = True
        elif not lazy:
            self.refresh()

    def refresh(self):
        block = self.steem.rpc.get_block(self.block)
        if not block:
            raise BlockDoesNotExistsException
        super(Block, self).__init__(block)
        self.cached = True

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(Block, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return super(Block, self).items()

    def time(self):
        return parse_time(self['timestamp'])
