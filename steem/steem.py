from .commit import Commit
from .steemd import Steemd
from steembase.exceptions import RPCError

class Steem:
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

    def __init__(self, nodes=None, no_broadcast=False, **kwargs):
        self.steemd = Steemd(
            nodes=nodes,
            **kwargs
        )
        self.commit = Commit(
            steemd_instance=self.steemd,
            no_broadcast=no_broadcast,
            **kwargs
        )

    def __getattr__(self, item):
        """ Bind .commit, .steemd methods here as a convenience. """
        if hasattr(self.steemd, item):
            return getattr(self.steemd, item)
        if hasattr(self.commit, item):
            return getattr(self.commit, item)
        if item.endswith("_api"):
            return Steem.Api(api_name=item, exec_method=self.steemd.exec)

        raise AttributeError('Steem has no attribute "%s"' % item)

    class Api(object):
        def __init__(self, api_name="", exec_method=None):
            self.api_name = api_name
            self.exec_method = exec_method
            return

        def __getattr__(self, method_name):
            return Steem.Method(
               api_name=self.api_name,
               method_name=method_name,
               exec_method=self.exec_method,
               )

    class Method(object):
        def __init__(self, api_name="", method_name="", exec_method=None):
            self.api_name = api_name
            self.method_name = method_name
            self.exec_method = exec_method
            return

        def __call__(self, *args, **kwargs):
            if len(kwargs) > 0:
                if len(args) > 0:
                    raise RPCError("Cannot specify both args and kwargs in RPC")
                return self.exec_method(self.method_name, kwargs=kwargs, api=self.api_name)
            return self.exec_method(self.method_name, *args, api=self.api_name)

if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
