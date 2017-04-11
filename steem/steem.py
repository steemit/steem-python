import logging

from steem.instance import shared_steemd_instance

from .commit import Commit
from .steemd import Steemd

# TODO:
# Steem() already supports node overloading, however, not trough defaults.
# ideally, we should be able to over-load this with:
# `steempy set nodes https://node1, https://node2`

class Steem(Steemd):
    """ Connect to the Steem network.

        Args:
            nodes (list): A list of Steem HTTP RPC nodes to connect to. If not provided, official Steemit nodes will be used.
            debug (bool): Elevate logging level to `logging.DEBUG`. Defaults to `logging.INFO`.
            no_broadcast (bool): If set to ``True``, committal actions like sending funds will have no effect (simulation only).


        Optional Arguments (kwargs):

        Args:
            keys (list): A list of wif keys. If provided, the Wallet will use these keys rather than the
                            ones found in BIP38 encrypted wallet.
            unsigned (bool): (Defaults to False) Use this for offline signing.
            expiration (int): (Defualts to 60) Size of window in seconds that the transaction
                                needs to be broadcasted in, before it expires.


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

        self.commit = Commit(
            steemd_instance=_steemd,
            no_broadcast=no_broadcast,
            **kwargs
        )

        # self._apply_commit_methods()

        super(Steem, self).__init__(nodes=nodes, log_level=_log_level, **kwargs)

    def __getattr__(self, item):
        """ Bind .commit methods here as a convenience. """
        if hasattr(self.commit, item):
            return getattr(self.commit, item)
        raise AttributeError('Steem has no attribute "%s"' % item)

    def _apply_commit_methods(self):
        """ Binds self.commit methods to this class for auto-complete purposes. """
        methods = [x for x in dir(self.commit)
                   if type(getattr(self.commit, x)).__name__ == 'method'
                   and not x.startswith('_')]
        for method_name in methods:
            to_call = getattr(self.commit, method_name)
            setattr(self, method_name, to_call)


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
