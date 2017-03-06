import sys
from functools import partial

api_methods = {
    "api": {
        "cancel_all_subscriptions": 0,
        "get_account_bandwidth": [('account', 'str'), ('bandwidth_type', 'object')],
        "get_account_count": [],
        "get_account_history": [('account', 'str'), ('index_from', 'int'), ('limit', 'int')],
        "get_account_references": [('account_name', 'str')],
        "get_account_votes": [('account', 'str')],
        "get_accounts": [('account_names', 'list')],
        "get_active_categories": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_active_votes": [('author', 'str'), ('permlink', 'str')],
        "get_active_witnesses": [],
        "get_best_categories": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_block": [('block_num', 'int')],
        "get_block_header": [('block_num', 'int')],
        "get_chain_properties": [],
        "get_config": [],
        "get_content": [('author', 'str'), ('permlink', 'str')],
        "get_content_replies": [('author', 'str'), ('permlink', 'str')],
        "get_conversion_requests": [('account', 'str')],
        "get_current_median_history_price": [],
        "get_discussions_by_active": [('discussion_query', 'dict')],
        "get_discussions_by_author_before_date": [('author', 'str'), ('start_permlink', 'str'), ('before_date', 'object'), ('limit', 'int')],
        "get_discussions_by_blog": [('discussion_query', 'dict')],
        "get_discussions_by_cashout": [('discussion_query', 'dict')],
        "get_discussions_by_children": [('discussion_query', 'dict')],
        "get_discussions_by_comments": [('discussion_query', 'dict')],
        "get_discussions_by_created": [('discussion_query', 'dict')],
        "get_discussions_by_feed": [('discussion_query', 'dict')],
        "get_discussions_by_hot": [('discussion_query', 'dict')],
        "get_discussions_by_payout": [('discussion_query', 'dict')],
        "get_discussions_by_promoted": [('discussion_query', 'dict')],
        "get_discussions_by_trending": [('discussion_query', 'dict')],
        "get_discussions_by_trending30": [('discussion_query', 'dict')],
        "get_discussions_by_votes": [('discussion_query', 'dict')],
        "get_dynamic_global_properties": [],
        "get_escrow": [('from_account', 'str'), ('escrow_id', 'int')],
        "get_expiring_vesting_delegations": [('author', 'str'), ('from_time', 'object'), ('limit', 'int')],  # ?
        "get_feed_history": [],
        "get_hardfork_version": [],
        "get_key_references": 0,  # deprecated, use account_by_key_api::get_key_references
        "get_liquidity_queue": [('start_account', 'str'), ('limit', 'int')],
        "get_miner_queue": [],
        "get_next_scheduled_hardfork": [],
        "get_open_orders": [('account', 'str')],
        "get_ops_in_block": [('block_num', 'int'), ('virtual_only', 'bool')],
        "get_order_book": [('limit', 'int')],
        "get_owner_history": [('account', 'str')],
        "get_potential_signatures": [('signed_transaction', 'object')],
        "get_recent_categories": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_recovery_request": [('account', 'str')],
        "get_replies_by_last_update": [('account', 'str'), ('start_permlink', 'str'), ('limit', 'int')],
        "get_required_signatures": [('signed_transaction', 'object'), ('available_keys', 'list')],
        "get_reward_fund": [('fund_name', 'str')],  # ?
        "get_savings_withdraw_from": [('account', 'str')],
        "get_savings_withdraw_to": [('account', 'str')],
        "get_state": [('path', 'str')],
        "get_tags_used_by_author": [('account', 'str')],
        "get_transaction": [('transaction_id', 'str')],
        "get_transaction_hex": [('signed_transaction', 'object')],
        "get_trending_categories": [('after', 'str'), ('limit', 'int')],
        "get_trending_tags": [('after', 'str'), ('limit', 'int')],
        "get_vesting_delegations": [('account', 'str'), ('from_account', 'str'), ('limit', 'int')],
        "get_withdraw_routes": [('account', 'str'), ('withdraw_route_type', 'str')],
        "get_witness_by_account": [('account', 'str')],
        "get_witness_count": [],
        "get_witness_schedule": [],
        "get_witnesses": [],
        "get_witnesses_by_vote": [('from_account', 'str'), ('limit', 'int')],
        "lookup_account_names": [('account_names', 'list')],
        "lookup_accounts": [('after', 'str'), ('limit', 'int')],
        "lookup_witness_accounts": [('account_name', 'str'), ('limit', 'int')],
        "set_block_applied_callback": 2,
        "set_pending_transaction_callback": 1,
        "set_subscribe_callback": 0,
        "verify_account_authority": [('account', 'str'), ('keys', 'list')],
        "verify_authority": [('signed_transaction', 'object')],
    }
}

method_template = """
def {method_name}(self{method_arguments}):
    return self.exec('{method_name}'{call_arguments})

"""


def steemd_codegen():
    """ Generates Python methods from steemd JSON API spec. Prints to stdout. """
    for method_name, method_signature in api_methods['api'].items():
        method_arg_mapper = partial(map, lambda x: ', %s: %s' % (x[0], x[1]))
        call_arg_mapper = partial(map, lambda x: ', %s' % x[0])

        # todo: remove this
        if type(method_signature) is int:
            continue

        # generate method code
        fn = method_template.format(
            method_name=method_name,
            method_arguments=''.join(method_arg_mapper(method_signature)),
            call_arguments=''.join(call_arg_mapper(method_signature)),
        )
        sys.stdout.write(fn)


if __name__ == '__main__':
    steemd_codegen()
