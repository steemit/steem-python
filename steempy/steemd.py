import sys
from functools import partial

api_methods = {
    "api": {
        "cancel_all_subscriptions": [],
        "get_account_bandwidth": 48,
        "get_account_count": [],
        "get_account_history": [('account', 'string')],
        "get_account_references": [('account_name', 'string')],
        "get_account_votes": [('account_name', 'string')],
        "get_accounts": [('account_names', 'list')],
        "get_active_categories": [('after', 'string'), ('limit', 'int')],  # deprecated?
        "get_active_votes": [('author', 'string'), ('permlink', 'string')],
        "get_active_witnesses": [],
        "get_best_categories": [('after', 'string'), ('limit', 'int')],  # deprecated?
        "get_block": [('block_num', 'int')],
        "get_block_header": [('block_num', 'int')],
        "get_chain_properties": [],
        "get_config": [],
        "get_content": [('author', 'string'), ('permlink', 'string')],
        "get_content_replies": [('author', 'string'), ('permlink', 'string')],
        "get_conversion_requests": [('account', 'string')],
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
        "lookup_accounts": [('after', 'string'), ('limit', 'int')],
        "lookup_witness_accounts": 71,
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
            method_signature = []

        # generate method code
        fn = method_template.format(
            method_name=method_name,
            method_arguments=''.join(method_arg_mapper(method_signature)),
            call_arguments=''.join(call_arg_mapper(method_signature)),
        )
        sys.stdout.write(fn)


if __name__ == '__main__':
    steemd_codegen()
