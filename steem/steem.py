import logging
from steem.instance import shared_steemd_instance

from .commit import Commit
from .steemd import Steemd
from .wallet import Wallet


class Steem(Steemd):
    """ Connect to the Steem network.

        Args:
            nodes (list): A list of Steem HTTP RPC nodes to connect to. If not provided, official Steemit nodes will be used.
            debug (bool): Elevate logging level to `logging.DEBUG`. Defaults to `logging.INFO`.
            no_broadcast (bool): If set to ``True``, committal actions like sending funds will have no effect (simulation only).

        Returns:
            Steemd class instance. It can be used to execute commands against steem node.

        Example:

           If you would like to override the official Steemit nodes (default), you can pass your own.
           When currently used node goes offline, ``Steemd`` will automatically fail-over to the next available node.

           .. code-block:: python

               nodes = [
                   'https://steemd.yournode1.com',
                   'https://steemd.yournode2.com',
               ]

               s = Steemd(nodes)

       """
    def __init__(self, nodes=None, debug=False, no_broadcast=False, **kwargs):
        _steemd = Steemd(nodes=nodes) if nodes else shared_steemd_instance()
        _log_level = logging.DEBUG if debug else logging.INFO
        self.commit = Commit(steemd_instance=_steemd,
                             debug=debug,
                             no_broadcast=no_broadcast,
                             **kwargs)
        self.wallet = Wallet(steemd_instance=_steemd, **kwargs)

        super(Steem, self).__init__(nodes=nodes, log_level=_log_level, **kwargs)


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())