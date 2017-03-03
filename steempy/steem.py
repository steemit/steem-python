# coding=utf-8
import concurrent.futures
import json
import logging
import os
import socket
from functools import partial
from urllib.parse import urlparse

import certifi
import urllib3
from urllib3.connection import HTTPConnection

logger = logging.getLogger(__name__)

api_methods = {
    "api": {
        "cancel_all_subscriptions": 3,
        "get_account_bandwidth": 48,
        "get_account_count": 41,
        "get_account_history": 43,
        "get_account_references": 38,
        "get_account_votes": 63,
        "get_accounts": 37,
        "get_active_categories": 25,
        "get_active_votes": 62,
        "get_active_witnesses": 73,
        "get_best_categories": 24,
        "get_block": 20,
        "get_block_header": 19,
        "get_chain_properties": 29,
        "get_config": 27,
        "get_content": 64,
        "get_content_replies": 65,
        "get_conversion_requests": 42,
        "get_current_median_history_price": 31,
        "get_discussions_by_active": 9,
        "get_discussions_by_author_before_date": 66,
        "get_discussions_by_blog": 16,
        "get_discussions_by_cashout": 10,
        "get_discussions_by_children": 13,
        "get_discussions_by_comments": 17,
        "get_discussions_by_created": 8,
        "get_discussions_by_feed": 15,
        "get_discussions_by_hot": 14,
        "get_discussions_by_payout": 11,
        "get_discussions_by_promoted": 18,
        "get_discussions_by_trending": 6,
        "get_discussions_by_trending30": 7,
        "get_discussions_by_votes": 12,
        "get_dynamic_global_properties": 28,
        "get_escrow": 46,
        "get_expiring_vesting_delegations": 52,
        "get_feed_history": 30,
        "get_hardfork_version": 33,
        "get_key_references": 36,
        "get_liquidity_queue": 55,
        "get_miner_queue": 74,
        "get_next_scheduled_hardfork": 34,
        "get_open_orders": 54,
        "get_ops_in_block": 21,
        "get_order_book": 53,
        "get_owner_history": 44,
        "get_potential_signatures": 59,
        "get_recent_categories": 26,
        "get_recovery_request": 45,
        "get_replies_by_last_update": 67,
        "get_required_signatures": 58,
        "get_reward_fund": 35,
        "get_savings_withdraw_from": 49,
        "get_savings_withdraw_to": 50,
        "get_state": 22,
        "get_tags_used_by_author": 5,
        "get_transaction": 57,
        "get_transaction_hex": 56,
        "get_trending_categories": 23,
        "get_trending_tags": 4,
        "get_vesting_delegations": 51,
        "get_withdraw_routes": 47,
        "get_witness_by_account": 69,
        "get_witness_count": 72,
        "get_witness_schedule": 32,
        "get_witnesses": 68,
        "get_witnesses_by_vote": 70,
        "lookup_account_names": 39,
        "lookup_accounts": 40,
        "lookup_witness_accounts": 71,
        "set_block_applied_callback": 2,
        "set_pending_transaction_callback": 1,
        "set_subscribe_callback": 0,
        "verify_account_authority": 61,
        "verify_authority": 60
    }
}


class RPCError(Exception):
    pass


class RPCConnectionError(Exception):
    pass


class Steem(object):
    """Simple Steem JSON-HTTP-RPC API

        This class serves as an abstraction layer for easy use of the
        Steem API.

    Args:
      str: url: url of the API server
      urllib3: HTTPConnectionPool url: instance of urllib3.HTTPConnectionPool

    .. code-block:: python

    from sbds.client import SimpleSteemAPIClient
    rpc = SimpleSteemAPIClient("http://domain.com:port")

    any call available to that port can be issued using the instance
    via the syntax rpc.exec_rpc('command', (*parameters*). Example:

    .. code-block:: python

    rpc.exec('info')

    Returns:

    """

    def __init__(self, url='https://steemd.steemitdev.com', log_level=logging.INFO, **kwargs):
        url = url or os.environ.get('STEEMD_HTTP_URL')
        self.url = url
        self.hostname = urlparse(url).hostname
        self.return_with_args = kwargs.get('return_with_args', False)
        self.re_raise = kwargs.get('re_raise', False)
        self.max_workers = kwargs.get('max_workers', None)

        num_pools = kwargs.get('num_pools', 10)
        maxsize = kwargs.get('maxsize', 10)
        timeout = kwargs.get('timeout', 30)
        retries = kwargs.get('retries', 10)
        pool_block = kwargs.get('pool_block', False)
        tcp_keepalive = kwargs.get('tcp_keepalive', True)

        if tcp_keepalive:
            socket_options = HTTPConnection.default_socket_options + \
                             [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1), ]
        else:
            socket_options = HTTPConnection.default_socket_options

        self.http = urllib3.poolmanager.PoolManager(
            num_pools=num_pools,
            maxsize=maxsize,
            block=pool_block,
            timeout=timeout,
            retries=retries,
            socket_options=socket_options,
            headers={'Content-Type': 'application/json'},
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
        '''
            urlopen(method, url, body=None, headers=None, retries=None,
            redirect=True, assert_same_host=True, timeout=<object object>,
            pool_timeout=None, release_conn=None, chunked=False, body_pos=None,
            **response_kw)
        '''
        self.request = partial(self.http.urlopen, 'POST', url)

        # auto-complete RPC API methods
        self.apply_helper_methods()

    def __getattr__(self, method_name):
        """ If method does not exist, lets try calling steemd with it. """
        return partial(self.exec, method_name)

    def apply_helper_methods(self):
        """ Binds known steemd api methods to this class for auto-complete purposes. """
        for method_name in api_methods['api'].keys():
            to_call = partial(self.exec, method_name)
            setattr(self, method_name, to_call)

    @staticmethod
    def json_rpc_body(name, *args, as_json=True):
        body_dict = {"method": name, "params": args, "jsonrpc": "2.0", "id": 0}
        if as_json:
            return json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        else:
            return body_dict

    def exec(self, name, *args, re_raise=None, return_with_args=None):
        body = Steem.json_rpc_body(name, *args)
        try:
            response = self.request(body=body)
        except Exception as e:
            if re_raise:
                raise e
            else:
                extra = dict(err=e, request=self.request)
                logger.info('Request error', extra=extra)
                self._return(
                    response=None,
                    args=args,
                    return_with_args=return_with_args)
        else:
            if response.status not in tuple(
                    [*response.REDIRECT_STATUSES, 200]):
                logger.info('non 200 response:%s', response.status)

            return self._return(
                response=response,
                args=args,
                return_with_args=return_with_args)

    def _return(self, response=None, args=None, return_with_args=None):
        return_with_args = return_with_args or self.return_with_args

        if not response:
            result = None
        else:
            try:
                response_json = json.loads(response.data.decode('utf-8'))
            except Exception as e:
                extra = dict(response=response, request_args=args, err=e)
                logger.info('failed to load response', extra=extra)
                result = None
            else:
                if 'error' in response_json:
                    error = response_json['error']
                    error_message = error.get(
                        'detail', response_json['error']['message'])
                    raise RPCError(error_message)

                result = response_json.get('result', None)
        if return_with_args:
            return result, args
        else:
            return result

    def exec_multi(self, name, params):
        body_gen = ({
                        "method": name,
                        "params": [i],
                        "jsonrpc": "2.0",
                        "id": 0
                    } for i in params)
        for body in body_gen:
            json_body = json.dumps(body, ensure_ascii=False).encode('utf8')
            yield self._return(
                response=self.request(body=json_body),
                args=body['params'],
                return_with_args=True)

    def exec_multi_with_futures(self, name, params, max_workers=None):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            # Start the load operations and mark each future with its URL
            futures = (executor.submit(self.exec, name, param)
                       for param in params)
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

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
        return self.exec('get_accounts', [account_name])


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
