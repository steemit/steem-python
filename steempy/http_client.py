# coding=utf-8
import concurrent.futures
import json
import logging
import socket
from functools import partial
from itertools import cycle
from urllib.parse import urlparse
import time

import certifi
import urllib3
from urllib3.connection import HTTPConnection
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)


class RPCError(Exception):
    pass


class RPCConnectionError(Exception):
    pass


class HttpClient(object):
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

    def __init__(self, nodes, log_level=logging.INFO, **kwargs):
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

        self.nodes = cycle(nodes)
        self.url = ''
        self.request = None
        self.change_node()

        logger.setLevel(log_level)

    def change_node(self):
        """ This method will change base URL of our requests.
        Use it when the current node goes down to change to a fallback node. """
        self.url = next(self.nodes)
        self.request = partial(self.http.urlopen, 'POST', self.url)

    @property
    def hostname(self):
        return urlparse(self.url).hostname

    @staticmethod
    def json_rpc_body(name, *args, as_json=True):
        body_dict = {"method": name, "params": args, "jsonrpc": "2.0", "id": 0}
        if as_json:
            return json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        else:
            return body_dict

    def exec(self, name, *args, re_raise=True, return_with_args=None, _ret_cnt=0):
        body = HttpClient.json_rpc_body(name, *args)
        try:
            response = self.request(body=body)
        except MaxRetryError as e:
            # try switching nodes before giving up
            if _ret_cnt > 2:
                time.sleep(5*_ret_cnt)
            elif _ret_cnt > 10:
                raise e
            self.change_node()
            return self.exec(name, *args,
                             re_raise=re_raise,
                             return_with_args=return_with_args,
                             _ret_cnt=_ret_cnt+1)
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
