import sys
from functools import partial
from pprint import pprint

from funcy.colls import where, pluck
from funcy.seqs import first, distinct, flatten
from steem import Steem

# todo
# "get_expiring_vesting_delegations": [('author', 'str'), ('from_time', 'object'), ('limit', 'int')],  # ?
# "get_reward_fund": [('fund_name', 'str')],  # ?

api_methods = [
    {
        'api': 'database_api',
        'method': 'set_subscribe_callback',
        'params': [('callback', 'object'), ('clear_filter', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'set_pending_transaction_callback',
        'params': [('callback', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'set_block_applied_callback',
        'params': [('callback', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'cancel_all_subscriptions',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_reward_fund',
        'params': [('fund_name', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_expiring_vesting_delegations',
        'params': [('account', 'str'), ('start', 'PointInTime'), ('limit',
                                                                  'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_trending_tags',
        'params': [('after_tag', 'str'), ('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_tags_used_by_author',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_trending',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_post_discussions_by_payout',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_comment_discussions_by_payout',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_created',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_active',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_cashout',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_payout',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_votes',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_children',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_hot',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_feed',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_blog',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_comments',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_discussions_by_promoted',
        'params': [('discussion_query', 'dict')],
    },
    {
        'api': 'database_api',
        'method': 'get_block_header',
        'params': [('block_num', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_block',
        'params': [('block_num', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_ops_in_block',
        'params': [('block_num', 'int'), ('virtual_only', 'bool')],
    },
    {
        'api': 'database_api',
        'method': 'get_state',
        'params': [('path', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_config',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_dynamic_global_properties',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_chain_properties',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_feed_history',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_current_median_history_price',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_witness_schedule',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_hardfork_version',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_next_scheduled_hardfork',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_accounts',
        'params': [('account_names', 'list')],
    },
    {
        'api': 'database_api',
        'method': 'get_account_references',
        'params': [('account_id', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'lookup_account_names',
        'params': [('account_names', 'list')],
    },
    {
        'api': 'database_api',
        'method': 'lookup_accounts',
        'params': [('after', 'str'), ('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_account_count',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_conversion_requests',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_account_history',
        'params': [('account', 'str'), ('index_from', 'int'), ('limit',
                                                               'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_owner_history',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_recovery_request',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_escrow',
        'params': [('from_account', 'str'), ('escrow_id', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_withdraw_routes',
        'params': [('account', 'str'), ('withdraw_route_type', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_account_bandwidth',
        'params': [('account', 'str'), ('bandwidth_type', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'get_savings_withdraw_from',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_savings_withdraw_to',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_order_book',
        'params': [('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_open_orders',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_liquidity_queue',
        'params': [('start_account', 'str'), ('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_transaction_hex',
        'params': [('signed_transaction', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'get_transaction',
        'params': [('transaction_id', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_required_signatures',
        'params': [('signed_transaction', 'object'), ('available_keys',
                                                      'list')],
    },
    {
        'api': 'database_api',
        'method': 'get_potential_signatures',
        'params': [('signed_transaction', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'verify_authority',
        'params': [('signed_transaction', 'object')],
    },
    {
        'api': 'database_api',
        'method': 'verify_account_authority',
        'params': [('account', 'str'), ('keys', 'list')],
    },
    {
        'api': 'database_api',
        'method': 'get_active_votes',
        'params': [('author', 'str'), ('permlink', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_account_votes',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_content',
        'params': [('author', 'str'), ('permlink', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_content_replies',
        'params': [('author', 'str'), ('permlink', 'str')],
    },
    {
        'api':
        'database_api',
        'method':
        'get_discussions_by_author_before_date',
        'params': [('author', 'str'), ('start_permlink', 'str'),
                   ('before_date', 'object'), ('limit', 'int')],
    },
    {
        'api':
        'database_api',
        'method':
        'get_replies_by_last_update',
        'params': [('account', 'str'), ('start_permlink', 'str'), ('limit',
                                                                   'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_witnesses',
        'params': [('witness_ids', 'list')]
    },
    {
        'api': 'database_api',
        'method': 'get_witness_by_account',
        'params': [('account', 'str')],
    },
    {
        'api': 'database_api',
        'method': 'get_witnesses_by_vote',
        'params': [('from_account', 'str'), ('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'lookup_witness_accounts',
        'params': [('from_account', 'str'), ('limit', 'int')],
    },
    {
        'api': 'database_api',
        'method': 'get_witness_count',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_active_witnesses',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_miner_queue',
        'params': [],
    },
    {
        'api': 'database_api',
        'method': 'get_vesting_delegations',
        'params': [('account', 'str'), ('from_account', 'str'), ('limit',
                                                                 'int')],
    },
    {
        'api': 'login_api',
        'method': 'login',
        'params': [('username', 'str'), ('password', 'str')],
    },
    {
        'api': 'login_api',
        'method': 'get_api_by_name',
        'params': [('api_name', 'str')],
    },
    {
        'api': 'login_api',
        'method': 'get_version',
        'params': [],
    },
    {
        'api':
        'follow_api',
        'method':
        'get_followers',
        'params': [('account', 'str'), ('start_follower', 'str'),
                   ('follow_type', 'str'), ('limit', 'int')],
    },
    {
        'api':
        'follow_api',
        'method':
        'get_following',
        'params': [('account', 'str'), ('start_follower', 'str'),
                   ('follow_type', 'str'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_follow_count',
        'params': [('account', 'str')],
    },
    {
        'api': 'follow_api',
        'method': 'get_feed_entries',
        'params': [('account', 'str'), ('entry_id', 'int'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_feed',
        'params': [('account', 'str'), ('entry_id', 'int'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_blog_entries',
        'params': [('account', 'str'), ('entry_id', 'int'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_blog',
        'params': [('account', 'str'), ('entry_id', 'int'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_account_reputations',
        'params': [('account', 'str'), ('limit', 'int')],
    },
    {
        'api': 'follow_api',
        'method': 'get_reblogged_by',
        'params': [('author', 'str'), ('permlink', 'str')],
    },
    {
        'api': 'follow_api',
        'method': 'get_blog_authors',
        'params': [('blog_account', 'str')],
    },
    {
        'api': 'network_broadcast_api',
        'method': 'broadcast_transaction',
        'params': [('signed_transaction', 'object')],
    },
    {
        'api': 'network_broadcast_api',
        'method': 'broadcast_transaction_with_callback',
        'params': [('callback', 'object'), ('signed_transaction', 'object')]
    },
    {
        'api': 'network_broadcast_api',
        'method': 'broadcast_transaction_synchronous',
        'params': [('signed_transaction', 'object')],
    },
    {
        'api': 'network_broadcast_api',
        'method': 'broadcast_block',
        'params': [('block', 'object')],
    },
    {
        'api': 'network_broadcast_api',
        'method': 'set_max_block_age',
        'params': [('max_block_age', 'int')],
    },
    {
        'api': 'market_history_api',
        'method': 'get_ticker',
        'params': [],
    },
    {
        'api': 'market_history_api',
        'method': 'get_volume',
        'params': [],
    },
    {
        'api': 'market_history_api',
        'method': 'get_order_book',
        'params': [('limit', 'int')],
    },
    {
        'api':
        'market_history_api',
        'method':
        'get_trade_history',
        'params': [('start', 'PointInTime'), ('end', 'PointInTime'), ('limit',
                                                                      'int')],
    },
    {
        'api': 'market_history_api',
        'method': 'get_recent_trades',
        'params': [('limit', 'int')],
        'returns': 'List[Any]',
    },
    {
        'api':
        'market_history_api',
        'method':
        'get_market_history',
        'params': [('bucket_seconds', 'int'), ('start', 'PointInTime'),
                   ('end', 'PointInTime')],
    },
    {
        'api': 'market_history_api',
        'method': 'get_market_history_buckets',
        'params': [],
    },
    {
        'api': 'account_by_key_api',
        'method': 'get_key_references',
        'params': [('public_keys', 'List[str]')],
    },
]

method_template = """
def {method_name}(self{method_arguments}){return_hints}:
    return self.exec('{method_name}'{call_arguments}, api='{api}')

"""


def steemd_codegen():
    """ Generates Python methods from steemd JSON API spec. Prints to stdout. """
    for endpoint in api_methods:
        method_arg_mapper = partial(map, lambda x: ', %s: %s' % (x[0], x[1]))
        call_arg_mapper = partial(map, lambda x: ', %s' % x[0])

        # skip unspecified calls
        if endpoint['params'] == 0:
            continue

        return_hints = ''
        if endpoint.get('returns'):
            return_hints = ' -> %s' % endpoint.get('returns')

        # generate method code
        fn = method_template.format(
            method_name=endpoint['method'],
            method_arguments=''.join(method_arg_mapper(endpoint['params'])),
            call_arguments=''.join(call_arg_mapper(endpoint['params'])),
            return_hints=return_hints,
            api=endpoint['api'])
        sys.stdout.write(fn)


def find_api(method_name):
    """ Given a method name, find its API. """
    endpoint = first(where(api_methods, method=method_name))
    if endpoint:
        return endpoint.get('api')


def inspect_steemd_implementation():
    """ Compare implemented methods with current live deployment of steemd. """
    _apis = distinct(pluck('api', api_methods))
    _methods = set(pluck('method', api_methods))

    avail_methods = []
    s = Steem(re_raise=False)
    for api in _apis:
        err = s.exec('nonexistentmethodcall', api=api)
        [
            avail_methods.append(x)
            for x in err['data']['stack'][0]['data']['api'].keys()
        ]

    avail_methods = set(avail_methods)

    print("\nMissing Methods:")
    pprint(avail_methods - _methods)

    print("\nLikely Deprecated Methods:")
    pprint(_methods - avail_methods)


if __name__ == '__main__':
    steemd_codegen()
    inspect_steemd_implementation()
