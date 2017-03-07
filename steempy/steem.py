# coding=utf-8
import logging
from functools import partial

from funcy import first

from .http_client import HttpClient
from .steemd import api_methods

logger = logging.getLogger(__name__)


class Steem(HttpClient):
    """ Connect to the Steem network.

        Args:
            nodes (list): A list of Steem HTTP RPC nodes to connect to. If not provided, official Steemit nodes will be used.
            log_level (int): Set the level for logging output. Defaults to `logging.INFO`.

        Returns:
            Steem class instance. It can be used to execute commands against steem node.

        Example:

           If you would like to override the official Steemit nodes (default), you can pass your own.
           When currently used node goes offline, ``Steem`` will automatically failover to the next available node.

           .. code-block:: python

               nodes = [
                   'https://steemd.yournode1.com',
                   'https://steemd.yournode2.com',
               ]

               s = Steem(nodes)

       """

    def __init__(self, nodes=None, log_level=logging.INFO, **kwargs):
        if not nodes:
            nodes = [
                'https://steemd.steemit.com',
                'https://steemd.steemitdev.com',
            ]

        # auto-complete missing RPC API methods
        # self._apply_missing_methods()

        super(Steem, self).__init__(nodes, log_level, **kwargs)

    def __getattr__(self, method_name):
        """ If method does not exist, lets try calling steemd with it. """
        logger.warning('Calling an unknown method "%s"' % method_name)
        return partial(self.exec, method_name)

    def _apply_missing_methods(self):
        """ Binds known steemd api methods to this class for auto-complete purposes. """
        for method_name in api_methods['api'].keys():
            if method_name not in dir(self):
                to_call = partial(self.exec, method_name)
                setattr(self, method_name, to_call)

    @property
    def last_irreversible_block_num(self):
        """ Newest irreversible block number. """
        return self.get_dynamic_global_properties()[
            'last_irreversible_block_num']

    @property
    def head_block_number(self):
        """ Newest block number. """
        return self.get_dynamic_global_properties()[
            'head_block_number']

    def get_account(self, account: str):
        """ Lookup account information such as user profile, public keys, balances, etc.

        Args:
            account (str): STEEM username that we are looking up.

        Returns:
            dict: Account information.

        """
        return first(self.exec('get_accounts', [account]))

    ################################
    # steemd api generated methods #
    ################################
    def set_subscribe_callback(self, callback: object, clear_filter: object):
        return self.exec('set_subscribe_callback', callback, clear_filter, api='database_api')

    def set_pending_transaction_callback(self, callback: object):
        return self.exec('set_pending_transaction_callback', callback, api='database_api')

    def set_block_applied_callback(self, callback: object):
        return self.exec('set_block_applied_callback', callback, api='database_api')

    def cancel_all_subscriptions(self):
        return self.exec('cancel_all_subscriptions', api='database_api')

    def get_trending_tags(self, after_tag: str, limit: int):
        return self.exec('get_trending_tags', after_tag, limit, api='database_api')

    def get_tags_used_by_author(self, account: str):
        return self.exec('get_tags_used_by_author', account, api='database_api')

    def get_discussions_by_trending(self, discussion_query: dict):
        return self.exec('get_discussions_by_trending', discussion_query, api='database_api')

    def get_discussions_by_trending30(self, discussion_query: dict):
        return self.exec('get_discussions_by_trending30', discussion_query, api='database_api')

    def get_discussions_by_created(self, discussion_query: dict):
        return self.exec('get_discussions_by_created', discussion_query, api='database_api')

    def get_discussions_by_active(self, discussion_query: dict):
        return self.exec('get_discussions_by_active', discussion_query, api='database_api')

    def get_discussions_by_cashout(self, discussion_query: dict):
        return self.exec('get_discussions_by_cashout', discussion_query, api='database_api')

    def get_discussions_by_payout(self, discussion_query: dict):
        return self.exec('get_discussions_by_payout', discussion_query, api='database_api')

    def get_discussions_by_votes(self, discussion_query: dict):
        return self.exec('get_discussions_by_votes', discussion_query, api='database_api')

    def get_discussions_by_children(self, discussion_query: dict):
        return self.exec('get_discussions_by_children', discussion_query, api='database_api')

    def get_discussions_by_hot(self, discussion_query: dict):
        return self.exec('get_discussions_by_hot', discussion_query, api='database_api')

    def get_discussions_by_feed(self, discussion_query: dict):
        return self.exec('get_discussions_by_feed', discussion_query, api='database_api')

    def get_discussions_by_blog(self, discussion_query: dict):
        return self.exec('get_discussions_by_blog', discussion_query, api='database_api')

    def get_discussions_by_comments(self, discussion_query: dict):
        return self.exec('get_discussions_by_comments', discussion_query, api='database_api')

    def get_discussions_by_promoted(self, discussion_query: dict):
        return self.exec('get_discussions_by_promoted', discussion_query, api='database_api')

    def get_block_header(self, block_num: int):
        """ Get block headers, given a block number.

        Args:
           block_num (int): Block number.

        Returns:
           dict: Block headers in a JSON compatible format.

        Example:

            .. code-block:: python

               s.get_block_headers(8888888)

            ::

                {'extensions': [],
                 'previous': '0087a2372163ff5c5838b09589ce281d5a564f66',
                 'timestamp': '2017-01-29T02:47:33',
                 'transaction_merkle_root': '4ddc419e531cccee6da660057d606d11aab9f3a5',
                 'witness': 'chainsquad.com'}
        """
        return self.exec('get_block_header', block_num, api='database_api')

    def get_block(self, block_num: int):
        """ Get the full block, transactions and all, given a block number.

        Args:
            block_num (int): Block number.

        Returns:
            dict: Block in a JSON compatible format.

        Example:

            .. code-block:: python

               s.get_block(8888888)

            ::

                {'extensions': [],
                 'previous': '0087a2372163ff5c5838b09589ce281d5a564f66',
                 'timestamp': '2017-01-29T02:47:33',
                 'transaction_merkle_root': '4ddc419e531cccee6da660057d606d11aab9f3a5',
                 'transactions': [{'expiration': '2017-01-29T02:47:42',
                   'extensions': [],
                   'operations': [['comment',
                     {'author': 'hilarski',
                      'body': 'https://media.giphy.com/media/RAx4Xwh1OPHji/giphy.gif',
                      'json_metadata': '{"tags":["motocross"],"image":["https://media.giphy.com/media/RAx4Xwh1OPHji/giphy.gif"],"app":"steemit/0.1"}',
                      'parent_author': 'b0y2k',
                      'parent_permlink': 'ama-supercross-round-4-phoenix-2017',
                      'permlink': 're-b0y2k-ama-supercross-round-4-phoenix-2017-20170129t024725575z',
                      'title': ''}]],
                   'ref_block_num': 41495,
                   'ref_block_prefix': 2639073901,
                   'signatures': ['2058b69f4c15f704a67a7b5a7996a9c9bbfd39c639f9db19b99ecad8328c4ce3610643f8d1b6424c352df120614cd535cd8f2772fce68814eeea50049684c37d69']}],
                 'witness': 'chainsquad.com',
                 'witness_signature': '1f115745e3f6fee95124164f4b57196c0eda2a700064faa97d0e037d3554ee2d5b618e6bfd457473783e8b8333724ba0bf93f0a4a7026e7925c8c4d2ba724152d4'}


        """
        return self.exec('get_block', block_num, api='database_api')

    def get_ops_in_block(self, block_num: int, virtual_only: bool):
        return self.exec('get_ops_in_block', block_num, virtual_only, api='database_api')

    def get_state(self, path: str):
        return self.exec('get_state', path, api='database_api')

    def get_trending_categories(self, after: str, limit: int):
        return self.exec('get_trending_categories', after, limit, api='database_api')

    def get_best_categories(self, after: str, limit: int):
        return self.exec('get_best_categories', after, limit, api='database_api')

    def get_active_categories(self, after: str, limit: int):
        return self.exec('get_active_categories', after, limit, api='database_api')

    def get_recent_categories(self, after: str, limit: int):
        return self.exec('get_recent_categories', after, limit, api='database_api')

    def get_config(self):
        """ Get internal chain configuration. """
        return self.exec('get_config', api='database_api')

    def get_dynamic_global_properties(self):
        return self.exec('get_dynamic_global_properties', api='database_api')

    def get_chain_properties(self):
        """ Get witness elected chain properties.

        ::

            {'account_creation_fee': '30.000 STEEM',
             'maximum_block_size': 65536,
             'sbd_interest_rate': 250}

        """
        return self.exec('get_chain_properties', api='database_api')

    def get_feed_history(self):
        """ Get the hourly averages of witness reported STEEM/SBD prices.

        ::

            {'current_median_history': {'base': '0.093 SBD', 'quote': '1.010 STEEM'},
             'id': 0,
             'price_history': [{'base': '0.092 SBD', 'quote': '1.010 STEEM'},
              {'base': '0.093 SBD', 'quote': '1.020 STEEM'},
              {'base': '0.093 SBD', 'quote': '1.010 STEEM'},
              {'base': '0.094 SBD', 'quote': '1.020 STEEM'},
              {'base': '0.093 SBD', 'quote': '1.010 STEEM'},

        """
        return self.exec('get_feed_history', api='database_api')

    def get_current_median_history_price(self):
        """ Get the average STEEM/SBD price.

        This price is based on moving average of witness reported price feeds.

        ::

            {'base': '0.093 SBD', 'quote': '1.010 STEEM'}

        """
        return self.exec('get_current_median_history_price', api='database_api')

    def get_witness_schedule(self):
        return self.exec('get_witness_schedule', api='database_api')

    def get_hardfork_version(self):
        """ Get the current version of the chain.

        Note:
            This is not the same as latest minor version.

        """
        return self.exec('get_hardfork_version', api='database_api')

    def get_next_scheduled_hardfork(self):
        return self.exec('get_next_scheduled_hardfork', api='database_api')

    def get_accounts(self, account_names: list):
        """ Lookup account information such as user profile, public keys, balances, etc.

        This method is same as ``get_account``, but supports querying for multiple accounts at the time.
        """
        return self.exec('get_accounts', account_names, api='database_api')

    def get_account_references(self, account_id: int):
        return self.exec('get_account_references', account_id, api='database_api')

    def lookup_account_names(self, account_names: list):
        return self.exec('lookup_account_names', account_names, api='database_api')

    def lookup_accounts(self, after: str, limit: int):
        return self.exec('lookup_accounts', after, limit, api='database_api')

    def get_account_count(self):
        """ How many accounts are currently registered on STEEM? """
        return self.exec('get_account_count', api='database_api')

    def get_conversion_requests(self, account: str):
        return self.exec('get_conversion_requests', account, api='database_api')

    def get_account_history(self, account: str, index_from: int, limit: int):
        """ History of all operations for a given account.

        Args:
           account (str): STEEM username that we are looking up.
           index_from (int): The highest database index we take as a starting point.
           limit (int): How many items are we interested in.

        Returns:
           list: List of operations.

        Example:
           To get the latest (newest) operations from a given user ``furion``, we should set the ``index_from`` to -1.
           This is the same as saying `give me the highest index there is`.

           .. code-block :: python

              s.get_account_history('furion', index_from=-1, limit=3)

           This will yield 3 recent operations like so:

           ::

              [[69974,
                {'block': 9941972,
                 'op': ['vote',
                  {'author': 'breezin',
                   'permlink': 'raising-children-is-not-childsplay-pro-s-and-con-s-of-being-a-young-parent',
                   'voter': 'furion',
                   'weight': 900}],
                 'op_in_trx': 0,
                 'timestamp': '2017-03-06T17:09:48',
                 'trx_id': '87f9176faccc7096b5ffb5d12bfdb41b3c0b2955',
                 'trx_in_block': 5,
                 'virtual_op': 0}],
               [69975,
                {'block': 9942005,
                 'op': ['curation_reward',
                  {'comment_author': 'leongkhan',
                   'comment_permlink': 'steem-investor-report-5-march-2017',
                   'curator': 'furion',
                   'reward': '112.397602 VESTS'}],
                 'op_in_trx': 1,
                 'timestamp': '2017-03-06T17:11:30',
                 'trx_id': '0000000000000000000000000000000000000000',
                 'trx_in_block': 5,
                 'virtual_op': 0}],
               [69976,
                {'block': 9942006,
                 'op': ['vote',
                  {'author': 'ejhaasteem',
                   'permlink': 'life-of-fishermen-in-aceh',
                   'voter': 'furion',
                   'weight': 100}],
                 'op_in_trx': 0,
                 'timestamp': '2017-03-06T17:11:30',
                 'trx_id': '955018ac8efe298bd90b45a4fbd15b9df7e00be4',
                 'trx_in_block': 7,
                 'virtual_op': 0}]]

           If we want to query for a particular range of indexes, we need to consider both `index_from` and `limit` fields.
           Remember, `index_from` works backwards, so if we set it to 100, we will get items `100, 99, 98, 97...`.

           For example, if we'd like to get the first 100 operations the user did, we would write:

           .. code-block:: python

              s.get_account_history('furion', index_from=100, limit=100)

           We can get the next 100 items by running:

           .. code-block:: python

              s.get_account_history('furion', index_from=200, limit=100)


        """
        return self.exec('get_account_history', account, index_from, limit, api='database_api')

    def get_owner_history(self, account: str):
        return self.exec('get_owner_history', account, api='database_api')

    def get_recovery_request(self, account: str):
        return self.exec('get_recovery_request', account, api='database_api')

    def get_escrow(self, from_account: str, escrow_id: int):
        return self.exec('get_escrow', from_account, escrow_id, api='database_api')

    def get_withdraw_routes(self, account: str, withdraw_route_type: str):
        return self.exec('get_withdraw_routes', account, withdraw_route_type, api='database_api')

    def get_account_bandwidth(self, account: str, bandwidth_type: object):
        return self.exec('get_account_bandwidth', account, bandwidth_type, api='database_api')

    def get_savings_withdraw_from(self, account: str):
        return self.exec('get_savings_withdraw_from', account, api='database_api')

    def get_savings_withdraw_to(self, account: str):
        return self.exec('get_savings_withdraw_to', account, api='database_api')

    def get_order_book(self, limit: int):
        """ Get the internal market order book.

        This method will return both bids and asks.

        Args:
            limit (int): How many levels deep into the book to show.

        Returns:
            dict: Order book.

        Example:

            .. code-block:: python

               s.get_order_book(2)

            Outputs:

            ::

                {'asks': [{'created': '2017-03-06T21:29:54',
                   'order_price': {'base': '513.571 STEEM', 'quote': '50.000 SBD'},
                   'real_price': '0.09735752213423265',
                   'sbd': 50000,
                   'steem': 513571},
                  {'created': '2017-03-06T21:01:39',
                   'order_price': {'base': '63.288 STEEM', 'quote': '6.204 SBD'},
                   'real_price': '0.09802806219188472',
                   'sbd': 6204,
                   'steem': 63288}],
                 'bids': [{'created': '2017-03-06T21:29:51',
                   'order_price': {'base': '50.000 SBD', 'quote': '516.503 STEEM'},
                   'real_price': '0.09680485882947436',
                   'sbd': 50000,
                   'steem': 516503},
                  {'created': '2017-03-06T17:30:24',
                   'order_price': {'base': '36.385 SBD', 'quote': '379.608 STEEM'},
                   'real_price': '0.09584887568228277',
                   'sbd': 36385,
                   'steem': 379608}]}


        """
        return self.exec('get_order_book', limit, api='database_api')

    def get_open_orders(self, account: str):
        return self.exec('get_open_orders', account, api='database_api')

    def get_liquidity_queue(self, start_account: str, limit: int):
        """ Get the liquidity queue.

        Warning:
            This feature is currently not in use, and might be deprecated in the future.

        """
        return self.exec('get_liquidity_queue', start_account, limit, api='database_api')

    def get_transaction_hex(self, signed_transaction: object):
        return self.exec('get_transaction_hex', signed_transaction, api='database_api')

    def get_transaction(self, transaction_id: str):
        return self.exec('get_transaction', transaction_id, api='database_api')

    def get_required_signatures(self, signed_transaction: object, available_keys: list):
        return self.exec('get_required_signatures', signed_transaction, available_keys, api='database_api')

    def get_potential_signatures(self, signed_transaction: object):
        return self.exec('get_potential_signatures', signed_transaction, api='database_api')

    def verify_authority(self, signed_transaction: object):
        return self.exec('verify_authority', signed_transaction, api='database_api')

    def verify_account_authority(self, account: str, keys: list):
        return self.exec('verify_account_authority', account, keys, api='database_api')

    def get_active_votes(self, author: str, permlink: str):
        """ Get all votes for the given post.

        Args:
            author (str): OP's STEEM username.
            permlink (str): Post identifier following the username. It looks like slug-ified title.

        Returns:
            list: List of votes.

        Example:
            .. code-block:: python

               s.get_active_votes('mynameisbrian', 'steemifying-idioms-there-s-no-use-crying-over-spilt-milk')

            Output:

            ::

               [{'percent': 10000,
                 'reputation': '36418980678',
                 'rshares': 356981288,
                 'time': '2017-03-06T20:04:18',
                 'voter': 'dailystuff',
                 'weight': '2287202760855'},
                 ...
                {'percent': 10000,
                 'reputation': 3386400109,
                 'rshares': 364252169,
                 'time': '2017-03-06T19:32:45',
                 'voter': 'flourish',
                 'weight': '2334690471157'}]
        """
        return self.exec('get_active_votes', author, permlink, api='database_api')

    def get_account_votes(self, account: str):
        """ All votes the given account ever made.

        Returned votes are in the following format:
        ::

           {'authorperm': 'alwaysfelicia/time-line-of-best-times-to-post-on-steemit-mystery-explained',
           'percent': 100,
           'rshares': 709227399,
           'time': '2016-08-07T16:06:24',
           'weight': '3241351576115042'},


        Args:
            account (str): STEEM username that we are looking up.

        Returns:
            list: List of votes.


        """
        return self.exec('get_account_votes', account, api='database_api')

    def get_content(self, author: str, permlink: str):
        return self.exec('get_content', author, permlink, api='database_api')

    def get_content_replies(self, author: str, permlink: str):
        return self.exec('get_content_replies', author, permlink, api='database_api')

    def get_discussions_by_author_before_date(self, author: str, start_permlink: str, before_date: object, limit: int):
        return self.exec('get_discussions_by_author_before_date', author, start_permlink, before_date, limit,
                         api='database_api')

    def get_replies_by_last_update(self, account: str, start_permlink: str, limit: int):
        return self.exec('get_replies_by_last_update', account, start_permlink, limit, api='database_api')

    def get_witnesses(self, witness_ids: list):
        return self.exec('get_witnesses', witness_ids, api='database_api')

    def get_witness_by_account(self, account: str):
        return self.exec('get_witness_by_account', account, api='database_api')

    def get_witnesses_by_vote(self, from_account: str, limit: int):
        return self.exec('get_witnesses_by_vote', from_account, limit, api='database_api')

    def lookup_witness_accounts(self, from_account: str, limit: int):
        return self.exec('lookup_witness_accounts', from_account, limit, api='database_api')

    def get_witness_count(self):
        return self.exec('get_witness_count', api='database_api')

    def get_active_witnesses(self):
        """ Get a list of currently active witnesses. """
        return self.exec('get_active_witnesses', api='database_api')

    def get_miner_queue(self):
        return self.exec('get_miner_queue', api='database_api')

    def get_vesting_delegations(self, account: str, from_account: str, limit: int):
        return self.exec('get_vesting_delegations', account, from_account, limit, api='database_api')

    def login(self, username: str, password: str):
        return self.exec('login', username, password, api='login_api')

    def get_api_by_name(self, api_name: str):
        return self.exec('get_api_by_name', api_name, api='login_api')

    def get_version(self):
        """ Get steemd version of the node currently connected to. """
        return self.exec('get_version', api='login_api')

    def get_followers(self, account: str, start_follower: str, follow_type: str, limit: int):
        return self.exec('get_followers', account, start_follower, follow_type, limit, api='follow_api')

    def get_following(self, account: str, start_follower: str, follow_type: str, limit: int):
        return self.exec('get_following', account, start_follower, follow_type, limit, api='follow_api')

    def get_follow_count(self, account: str):
        return self.exec('get_follow_count', account, api='follow_api')

    def get_feed_entries(self, account: str, entry_id: int, limit: int):
        return self.exec('get_feed_entries', account, entry_id, limit, api='follow_api')

    def get_feed(self, account: str, entry_id: int, limit: int):
        return self.exec('get_feed', account, entry_id, limit, api='follow_api')

    def get_blog_entries(self, account: str, entry_id: int, limit: int):
        return self.exec('get_blog_entries', account, entry_id, limit, api='follow_api')

    def get_blog(self, account: str, entry_id: int, limit: int):
        return self.exec('get_blog', account, entry_id, limit, api='follow_api')

    def get_account_reputations(self, account: str, limit: int):
        return self.exec('get_account_reputations', account, limit, api='follow_api')

    def get_reblogged_by(self, author: str, permlink: str):
        return self.exec('get_reblogged_by', author, permlink, api='follow_api')

    def get_blog_authors(self, blog_account: str):
        return self.exec('get_blog_authors', blog_account, api='follow_api')

    def broadcast_transaction(self, signed_transaction: object):
        return self.exec('broadcast_transaction', signed_transaction, api='network_broadcast_api')

    def broadcast_transaction_with_callback(self, callback: object, signed_transaction: object):
        return self.exec('broadcast_transaction_with_callback', callback, signed_transaction,
                         api='network_broadcast_api')

    def broadcast_transaction_synchronous(self, signed_transaction: object):
        return self.exec('broadcast_transaction_synchronous', signed_transaction, api='network_broadcast_api')

    def broadcast_block(self, block: object):
        return self.exec('broadcast_block', block, api='network_broadcast_api')

    def set_max_block_age(self, max_block_age: int):
        return self.exec('set_max_block_age', max_block_age, api='network_broadcast_api')


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
