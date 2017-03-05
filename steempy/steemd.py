import sys
from functools import partial

api_methods = {
    "api": {
        "cancel_all_subscriptions": [],
        "get_account_bandwidth": 48,
        "get_account_count": [],
        "get_account_history": [('account', 'str')],
        "get_account_references": [('account_name', 'str')],
        "get_account_votes": [('account_name', 'str')],
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
        "get_dynamic_global_properties": [],
        "get_escrow": [('from_account', 'str'), ('escrow_id', 'int')],
        "get_expiring_vesting_delegations": [('author', 'str'), ('from_time', 'time_point_sec'), ('limit', 'int')],  # ?
        "get_feed_history": [],
        "get_hardfork_version": [],
        "get_key_references": [('public_key', 'str')],
        "get_liquidity_queue": [('start_account', 'str'), ('limit', 'int')],
        "get_miner_queue": [],
        "get_next_scheduled_hardfork": [],
        "get_open_orders": [('account', 'str')],
        "get_ops_in_block": [('block_num', 'int'), ('virtual_only', 'bool')],
        "get_order_book": [('limit', 'int')],
        "get_owner_history": [('account', 'str')],
        "get_potential_signatures": 59,
        "get_recent_categories": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_recovery_request": [('account', 'str')],
        "get_replies_by_last_update": 67,
        "get_required_signatures": 58,
        "get_reward_fund": [('fund_name', 'str')],  # ?
        "get_savings_withdraw_from": [('account', 'str')],
        "get_savings_withdraw_to": [('account', 'str')],
        "get_state": [('path', 'str')],
        "get_tags_used_by_author": [('account', 'str')],
        "get_transaction": 57,
        "get_transaction_hex": 56,
        "get_trending_categories": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_trending_tags": [('after', 'str'), ('limit', 'int')],  # deprecated?
        "get_vesting_delegations": [('account', 'str'), ('from_account', 'str'), ('limit', 'int')],
        "get_withdraw_routes": 47,
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
        "verify_account_authority": 61,
        "verify_authority": 60
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
