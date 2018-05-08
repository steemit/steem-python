# coding=utf-8
import json
import logging
import socket
import time
import sys
from functools import partial
from itertools import cycle
import concurrent.futures
import certifi
import urllib3
from steembase.exceptions import RPCError, RPCErrorRecoverable
from urllib3.connection import HTTPConnection
from urllib3.exceptions import MaxRetryError, ReadTimeoutError, ProtocolError

if sys.version >= '3.0':
    from http.client import RemoteDisconnected
    from urllib.parse import urlparse
else:
    from urlparse import urlparse
    from httplib import HTTPException

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

    # set of endpoints which were detected to not support condenser_api
    non_appbase_nodes = set()

    def __init__(self, nodes, **kwargs):
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

        self.nodes = cycle(self.sanitize_nodes(nodes))
        self.url = ''
        self.request = None
        self.next_node()

        log_level = kwargs.get('log_level', logging.INFO)
        logger.setLevel(log_level)

    def _curr_node_downgraded(self):
        return self.url in HttpClient.non_appbase_nodes

    def _downgrade_curr_node(self):
        HttpClient.non_appbase_nodes.add(self.url)

    def _is_error_recoverable(self, error):
        assert 'message' in error, "missing error msg key: {}".format(error)
        assert 'code' in error, "missing error code key: {}".format(error)
        message = error['message']
        code = error['code']

        # common steemd error
        # {"code"=>-32003, "message"=>"Unable to acquire database lock"}
        if message == 'Unable to acquire database lock':
            return True

        # rare steemd error
        # {"code"=>-32000, "message"=>"Unknown exception", "data"=>"0 exception: unspecified\nUnknown Exception\n[...]"}
        if message == 'Unknown exception':
            return True

        # generic jussi error
        # {'code': -32603, 'message': 'Internal Error', 'data': {'error_id': 'c7a15140-f306-4727-acbd-b5e8f3717e9b',
        #         'request': {'amzn_trace_id': 'Root=1-5ad4cb9f-9bc86fbca98d9a180850fb80', 'jussi_request_id': None}}}
        if message == 'Internal Error' and code == -32603:
            return True

        return False

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
    def json_rpc_body(name, *args, **kwargs):
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

        # if kwargs is non-empty after this, it becomes the call params
        as_json = kwargs.pop('as_json', True)
        api = kwargs.pop('api', None)
        _id = kwargs.pop('_id', 0)

        # `kwargs` for object-style param, `args` for list-style. pick one.
        assert not (kwargs and args), 'fail - passed array AND object args'
        params = kwargs if kwargs else args

        if api:
            body = {'jsonrpc': '2.0',
                    'id': _id,
                    'method': 'call',
                    'params': [api, name, params]}
        else:
            body = {'jsonrpc': '2.0',
                    'id': _id,
                    'method': name,
                    'params': params}

        if as_json:
            return json.dumps(body, ensure_ascii=False).encode('utf8')

        return body

    def call(self,
             name,
             *args,
             **kwargs):
        """ Call a remote procedure in steemd.

        Warnings:

            This command will auto-retry in case of node failure, as well
            as handle node fail-over.

        """

        # tuple of Exceptions which are eligible for retry
        retry_exceptions = (MaxRetryError, ReadTimeoutError,
                            ProtocolError, RPCErrorRecoverable,)

        if sys.version > '3.5':
            retry_exceptions += (json.decoder.JSONDecodeError,)
        else:
            retry_exceptions += (ValueError,)

        if sys.version > '3.0':
            retry_exceptions += (RemoteDisconnected, ConnectionResetError,)
        else:
            retry_exceptions += (HTTPException,)

        tries = 0
        while True:
            try:

                body_kwargs = kwargs.copy()
                if not self._curr_node_downgraded():
                    body_kwargs['api'] = 'condenser_api'

                body = HttpClient.json_rpc_body(name, *args, **body_kwargs)
                response = self.request(body=body)

                success_codes = tuple(list(response.REDIRECT_STATUSES) + [200])
                if response.status not in success_codes:
                    raise RPCErrorRecoverable("non-200 response: %s from %s"
                                              % (response.status, self.hostname))

                result = json.loads(response.data.decode('utf-8'))
                assert result, 'result entirely blank'

                if 'error' in result:
                    # legacy (pre-appbase) nodes always return err code 1
                    legacy = result['error']['code'] == 1
                    detail = result['error']['message']

                    # some errors have no data key (db lock error)
                    if 'data' not in result['error']:
                        error = 'error'
                    # some errors have no name key (jussi errors)
                    elif 'name' not in result['error']['data']:
                        error = 'unspecified error'
                    else:
                        error = result['error']['data']['name']

                    if legacy:
                        detail = ":".join(detail.split("\n")[0:2])
                        if not self._curr_node_downgraded():
                            self._downgrade_curr_node()
                            logging.error('Downgrade-retry %s', self.hostname)
                            continue

                    detail = ('%s from %s (%s) in %s' % (
                        error, self.hostname, detail, name))

                    if self._is_error_recoverable(result['error']):
                        raise RPCErrorRecoverable(detail)
                    else:
                        raise RPCError(detail)

                return result['result']

            except retry_exceptions as e:
                if e == ValueError and 'JSON' not in e.args[0]:
                    raise e  # (python<3.5 lacks json.decoder.JSONDecodeError)
                if tries >= 10:
                    logging.error('Failed after %d attempts -- %s: %s',
                                  tries, e.__class__.__name__, e)
                    raise e
                tries += 1
                logging.warning('Retry in %ds -- %s: %s', tries,
                                e.__class__.__name__, e)
                time.sleep(tries)
                self.next_node()
                continue

            # TODO: unclear why this case is here; need to explicitly
            #       define exceptions for which we refuse to retry.
            except Exception as e:
                extra = dict(err=e, request=self.request)
                logger.error('Unexpected exception! Please report at ' +
                             'https://github.com/steemit/steem-python/issues' +
                             ' -- %s: %s', e.__class__.__name__, e, extra=extra)
                raise e

    def call_multi_with_futures(self, name, params, api=None,
                                max_workers=None):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            # Start the load operations and mark each future with its URL
            def ensure_list(val):
                return val if isinstance(val, (list, tuple, set)) else [val]

            futures = (executor.submit(
                self.call, name, *ensure_list(param), api=api)
                for param in params)
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

    def sanitize_nodes(self, nodes):
        """

        This method is designed to explicitly validate the user defined
        nodes that are passed to http_client. If left unvalidated, improper
        input causes a variety of explicit-to-red herring errors in the code base.
        This will fail loudly in the event that incorrect input has been passed.

        There are three types of input allowed when defining nodes.
        1. a string of a single node url. ie nodes='https://api.steemit.com'
        2. a comma separated string of several node url's.
            nodes='https://api.steemit.com,<<community node>>,<<your personal node>>'
        3. a list of string node url's.
            nodes=['https://api.steemit.com','<<community node>>','<<your personal node>>']

        Any other input will result in a ValueError being thrown.

        :param nodes: the nodes argument passed to http_client
        :return: a list of node url's.
        """

        if self._isString(nodes):
            nodes = nodes.split(',')
        elif isinstance(nodes, list):
            if not all(self._isString(node) for node in nodes):
                raise ValueError("All nodes in list must be a string.")
        else:
            raise ValueError("nodes arg must be a "
                             "comma separated string of node url's, "
                             "a single string url, "
                             "or a list of strings.")

        return nodes

    def _isString(self, input):
        return isinstance(input, str) or \
               (sys.version < '3.0' and isinstance(input, unicode))
