# coding=utf-8
import concurrent.futures
import json
import logging
import socket
import time
from functools import partial
from itertools import cycle

import certifi
import urllib3
from steembase.exceptions import RPCError
from urllib3.connection import HTTPConnection
from urllib3.exceptions import MaxRetryError, ReadTimeoutError, ProtocolError

logger = logging.getLogger(__name__)


class HttpClient(object):
    """ Simple Steem JSON-HTTP-RPC API

    This class serves as an abstraction layer for easy use of the Steem API.

    Args:
      nodes (list): A list of Steem HTTP RPC nodes to connect to.

    .. code-block:: python

       from steem.http_client import HttpClient

       rpc = HttpClient(['https://steemd-node1.com',
       'https://steemd-node2.com'])

    any call available to that port can be issued using the instance
    via the syntax ``rpc.call('command', *parameters)``.

    Example:

    .. code-block:: python

       rpc.call(
           'get_followers',
           'furion', 'abit', 'blog', 10,
           api='follow_api'
       )

    """

    def __init__(self, nodes, **kwargs):
        self.return_with_args = kwargs.get('return_with_args', False)
        self.re_raise = kwargs.get('re_raise', True)
        self.max_workers = kwargs.get('max_workers', None)

        num_pools = kwargs.get('num_pools', 10)
        maxsize = kwargs.get('maxsize', 10)
        timeout = kwargs.get('timeout', 60)
        retries = kwargs.get('retries', 20)
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
        self.next_node()

        log_level = kwargs.get('log_level', logging.INFO)
        logger.setLevel(log_level)

    def next_node(self):
        """ Switch to the next available node.

        This method will change base URL of our requests.

        Use it when the current node goes down to change to a fallback
        node.

        """
        self.set_node(next(self.nodes))

    def set_node(self, node_url):
        """ Change current node to provided node URL. """
        self.url = node_url
        self.request = partial(self.http.urlopen, 'POST', self.url)

    @property
    def hostname(self):
        return urlparse(self.url).hostname

    @staticmethod
    def json_rpc_body(name, api=None, as_json=True, _id=0, kwargs=None, *args):
        """ Build request body for steemd RPC requests.

        Args:

            name (str): Name of a method we are trying to call. (ie:
            `get_accounts`)

            args: A list of arguments belonging to the calling method.

            api (None, str): If api is provided (ie: `follow_api`),
             we generate a body that uses `call` method appropriately.

            as_json (bool): Should this function return json as dictionary
            or string.

            _id (int): This is an arbitrary number that can be used for
            request/response tracking in multi-threaded scenarios.

        Returns:

            (dict,str): If `as_json` is set to `True`, we get json
            formatted as a string.

            Otherwise, a Python dictionary is returned.

        """
        print(name)
        headers = {"jsonrpc": "2.0", "id": _id}
        if kwargs is not None:
            body_dict = headers.update({"method": "call",
                         "params": [api, name, kwargs]})
        elif api:
            body_dict = headers.update({"method": "call",
                         "params": [api, name, args]})
        else:
            body_dict = headers.update({"method": name, "params": args})
        if as_json:
            return json.dumps(body_dict, ensure_ascii=False).encode('utf8')
        else:
            print(body_dict)
            return body_dict

    def call(self,
             name,
             api=None,
             return_with_args=None,
             _ret_cnt=0,
             kwargs=None,
             *args):
        """ Call a remote procedure in steemd.

        Warnings:

            This command will auto-retry in case of node failure, as well
            as handle node fail-over, unless we are broadcasting a
            transaction.  In latter case, the exception is **re-raised**.

        """
        body = HttpClient.json_rpc_body(name, *args, api=api, kwargs=kwargs)
        response = None
        print(args)
        try:
            response = self.request(body=body)
        except (MaxRetryError, ConnectionResetError, ReadTimeoutError,
                RemoteDisconnected, ProtocolError) as e:
            # if we broadcasted a transaction, always raise
            # this is to prevent potential for double spend scenario
            if api == 'network_broadcast_api':
                raise e

            # try switching nodes before giving up
            if _ret_cnt > 2:
                # we should wait only a short period before trying
                # the next node, but still slowly increase backoff
                time.sleep(_ret_cnt)
            if _ret_cnt > 10:
                raise e
            self.next_node()
            logging.debug('Switched node to %s due to exception: %s' %
                          (self.hostname, e.__class__.__name__))
            return self.call(
                name,
                *args,
                return_with_args=return_with_args,
                _ret_cnt=_ret_cnt + 1)
        except Exception as e:
            if self.re_raise:
                raise e
            else:
                extra = dict(err=e, request=self.request)
                logger.info('Request error', extra=extra)
                return self._return(
                    response=response,
                    args=args,
                    return_with_args=return_with_args)
        else:
            # redirectStatuses = list(response.REDIRECT_STATUSES)
            # redirectStatuses.append(200)
            if response.status not in tuple([*response.REDIRECT_STATUSES, 200]):
                logger.info('non 200 response:%s', response.status)

            return self._return(
                response=response,
                args=args,
                return_with_args=return_with_args)

    def _return(self, response=None, args=None, return_with_args=None):
        return_with_args = return_with_args or self.return_with_args
        result = None

        if response:
            try:
                response_json = json.loads(response.data.decode('utf-8'))
            except Exception as e:
                extra = dict(response=response, request_args=args, err=e)
                logger.info('failed to load response', extra=extra)
                result = None
            else:
                if 'error' in response_json:
                    print(response_json)
                    error = response_json['error']

                    if self.re_raise:
                        error_message = error.get(
                            'detail', response_json['error']['message'])
                        raise RPCError(error_message)

                    result = response_json['error']
                else:
                    result = response_json.get('result', None)
        if return_with_args:
            return result, args
        else:
            return result

    def call_multi_with_futures(self, name, params, api=None,
                                max_workers=None):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            # Start the load operations and mark each future with its URL
            def ensure_list(parameter):
                return parameter if type(parameter) in (list, tuple,
                                                        set) else [parameter]

            futures = (executor.submit(
                self.call, name, *ensure_list(param), api=api)
                       for param in params)
            for future in concurrent.futures.as_completed(futures):
                yield future.result()
