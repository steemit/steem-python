import logging
from steem.instance import shared_steemd_instance

from .commit import Commit
from .steemd import Steemd
from .wallet import Wallet


class Steem(Steemd):

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