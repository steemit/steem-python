# coding=utf-8
import logging
import os
from functools import partial

from funcy import first

from .http_client import HttpClient
from .steemd import api_methods

logger = logging.getLogger(__name__)


class Steem(HttpClient):
    """ Docstring
    """

    def __init__(self, url='https://steemd.steemitdev.com', log_level=logging.INFO, **kwargs):
        url = url or os.environ.get('STEEMD_HTTP_URL')

        # auto-complete RPC API methods
        self.apply_helper_methods()

        super(Steem, self).__init__(url, log_level, **kwargs)

    def __getattr__(self, method_name):
        """ If method does not exist, lets try calling steemd with it. """
        logger.warning('Calling an unknown method "%s"' % method_name)
        return partial(self.exec, method_name)

    def apply_helper_methods(self):
        """ Binds known steemd api methods to this class for auto-complete purposes. """
        for method_name in api_methods['api'].keys():
            to_call = partial(self.exec, method_name)
            setattr(self, method_name, to_call)

    @property
    def last_irreversible_block_num(self):
        return self.get_dynamic_global_properties()[
            'last_irreversible_block_num']

    @property
    def head_block_height(self):
        return self.get_dynamic_global_properties()[
            'last_irreversible_block_num']

    @property
    def block_height(self):
        return self.get_dynamic_global_properties()[
            'last_irreversible_block_num']

    def get_account(self, account_name):
        return first(self.exec('get_accounts', [account_name]))


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
