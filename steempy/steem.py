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

    def __init__(self, nodes=None, log_level=logging.INFO, **kwargs):
        if not nodes:
            nodes = [
                'https://steemd.steemit.com',
                'https://steemd.steemitdev.com',
            ]

        # auto-complete missing RPC API methods
        self.apply_missing_methods()

        super(Steem, self).__init__(nodes, log_level, **kwargs)

    def __getattr__(self, method_name):
        """ If method does not exist, lets try calling steemd with it. """
        logger.warning('Calling an unknown method "%s"' % method_name)
        return partial(self.exec, method_name)

    def apply_missing_methods(self):
        """ Binds known steemd api methods to this class for auto-complete purposes. """
        for method_name in api_methods['api'].keys():
            if method_name not in dir(self):
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

    def get_account(self, account: str):
        """ Lookup account information, user profile, public keys, balances, etc.

        Args:
            account: STEEM username that we are looking up.

        Returns:
            dict: Account information.

        """
        return first(self.exec('get_accounts', [account]))

    def get_account_bandwidth(self, account: str, bandwidth_type: object):
        return self.exec('get_account_bandwidth', account, bandwidth_type)

    def get_account_count(self):
        return self.exec('get_account_count')

    def get_account_history(self, account: str):
        return self.exec('get_account_history', account)

    def get_account_references(self, account_name: str):
        return self.exec('get_account_references', account_name)

    def get_account_votes(self, account_name: str):
        return self.exec('get_account_votes', account_name)

    def get_accounts(self, account_names: list):
        return self.exec('get_accounts', account_names)

    def get_active_categories(self, after: str, limit: int):
        return self.exec('get_active_categories', after, limit)

    def get_active_votes(self, author: str, permlink: str):
        return self.exec('get_active_votes', author, permlink)

    def get_active_witnesses(self):
        return self.exec('get_active_witnesses')

    def get_best_categories(self, after: str, limit: int):
        return self.exec('get_best_categories', after, limit)

    def get_block(self, block_num: int):
        return self.exec('get_block', block_num)

    def get_block_header(self, block_num: int):
        return self.exec('get_block_header', block_num)

    def get_chain_properties(self):
        return self.exec('get_chain_properties')

    def get_config(self):
        return self.exec('get_config')

    def get_content(self, author: str, permlink: str):
        return self.exec('get_content', author, permlink)

    def get_content_replies(self, author: str, permlink: str):
        return self.exec('get_content_replies', author, permlink)

    def get_conversion_requests(self, account: str):
        return self.exec('get_conversion_requests', account)

    def get_current_median_history_price(self):
        return self.exec('get_current_median_history_price')

    def get_discussions_by_active(self, discussion_query: dict):
        return self.exec('get_discussions_by_active', discussion_query)

    def get_discussions_by_author_before_date(self, author: str, start_permlink: str, before_date: object, limit: int):
        return self.exec('get_discussions_by_author_before_date', author, start_permlink, before_date, limit)

    def get_discussions_by_blog(self, discussion_query: dict):
        return self.exec('get_discussions_by_blog', discussion_query)

    def get_discussions_by_cashout(self, discussion_query: dict):
        return self.exec('get_discussions_by_cashout', discussion_query)

    def get_discussions_by_children(self, discussion_query: dict):
        return self.exec('get_discussions_by_children', discussion_query)

    def get_discussions_by_comments(self, discussion_query: dict):
        return self.exec('get_discussions_by_comments', discussion_query)

    def get_discussions_by_created(self, discussion_query: dict):
        return self.exec('get_discussions_by_created', discussion_query)

    def get_discussions_by_feed(self, discussion_query: dict):
        return self.exec('get_discussions_by_feed', discussion_query)

    def get_discussions_by_hot(self, discussion_query: dict):
        return self.exec('get_discussions_by_hot', discussion_query)

    def get_discussions_by_payout(self, discussion_query: dict):
        return self.exec('get_discussions_by_payout', discussion_query)

    def get_discussions_by_promoted(self, discussion_query: dict):
        return self.exec('get_discussions_by_promoted', discussion_query)

    def get_discussions_by_trending(self, discussion_query: dict):
        return self.exec('get_discussions_by_trending', discussion_query)

    def get_discussions_by_trending30(self, discussion_query: dict):
        return self.exec('get_discussions_by_trending30', discussion_query)

    def get_discussions_by_votes(self, discussion_query: dict):
        return self.exec('get_discussions_by_votes', discussion_query)

    def get_dynamic_global_properties(self):
        return self.exec('get_dynamic_global_properties')

    def get_escrow(self, from_account: str, escrow_id: int):
        return self.exec('get_escrow', from_account, escrow_id)

    def get_expiring_vesting_delegations(self, author: str, from_time: object, limit: int):
        return self.exec('get_expiring_vesting_delegations', author, from_time, limit)

    def get_feed_history(self):
        return self.exec('get_feed_history')

    def get_hardfork_version(self):
        return self.exec('get_hardfork_version')

    def get_key_references(self, public_key: str):
        return self.exec('get_key_references', public_key)

    def get_liquidity_queue(self, start_account: str, limit: int):
        return self.exec('get_liquidity_queue', start_account, limit)

    def get_miner_queue(self):
        return self.exec('get_miner_queue')

    def get_next_scheduled_hardfork(self):
        return self.exec('get_next_scheduled_hardfork')

    def get_open_orders(self, account: str):
        return self.exec('get_open_orders', account)

    def get_ops_in_block(self, block_num: int, virtual_only: bool):
        return self.exec('get_ops_in_block', block_num, virtual_only)

    def get_order_book(self, limit: int):
        return self.exec('get_order_book', limit)

    def get_owner_history(self, account: str):
        return self.exec('get_owner_history', account)

    def get_potential_signatures(self, signed_transaction: object):
        return self.exec('get_potential_signatures', signed_transaction)

    def get_recent_categories(self, after: str, limit: int):
        return self.exec('get_recent_categories', after, limit)

    def get_recovery_request(self, account: str):
        return self.exec('get_recovery_request', account)

    def get_replies_by_last_update(self, account: str, start_permlink: str, limit: int):
        return self.exec('get_replies_by_last_update', account, start_permlink, limit)

    def get_required_signatures(self, signed_transaction: object, available_keys: list):
        return self.exec('get_required_signatures', signed_transaction, available_keys)

    def get_reward_fund(self, fund_name: str):
        return self.exec('get_reward_fund', fund_name)

    def get_savings_withdraw_from(self, account: str):
        return self.exec('get_savings_withdraw_from', account)

    def get_savings_withdraw_to(self, account: str):
        return self.exec('get_savings_withdraw_to', account)

    def get_state(self, path: str):
        return self.exec('get_state', path)

    def get_tags_used_by_author(self, account: str):
        return self.exec('get_tags_used_by_author', account)

    def get_transaction(self, transaction_id: str):
        return self.exec('get_transaction', transaction_id)

    def get_transaction_hex(self, signed_transaction: object):
        return self.exec('get_transaction_hex', signed_transaction)

    def get_trending_categories(self, after: str, limit: int):
        return self.exec('get_trending_categories', after, limit)

    def get_trending_tags(self, after: str, limit: int):
        return self.exec('get_trending_tags', after, limit)

    def get_vesting_delegations(self, account: str, from_account: str, limit: int):
        return self.exec('get_vesting_delegations', account, from_account, limit)

    def get_withdraw_routes(self, account: str, withdraw_route_type: str):
        return self.exec('get_withdraw_routes', account, withdraw_route_type)

    def get_witness_by_account(self, account: str):
        return self.exec('get_witness_by_account', account)

    def get_witness_count(self):
        return self.exec('get_witness_count')

    def get_witness_schedule(self):
        return self.exec('get_witness_schedule')

    def get_witnesses(self):
        return self.exec('get_witnesses')

    def get_witnesses_by_vote(self, from_account: str, limit: int):
        return self.exec('get_witnesses_by_vote', from_account, limit)

    def lookup_account_names(self, account_names: list):
        return self.exec('lookup_account_names', account_names)

    def lookup_accounts(self, after: str, limit: int):
        return self.exec('lookup_accounts', after, limit)

    def lookup_witness_accounts(self, account_name: str, limit: int):
        return self.exec('lookup_witness_accounts', account_name, limit)

    def verify_account_authority(self, account: str, keys: list):
        return self.exec('verify_account_authority', account, keys)

    def verify_authority(self, signed_transaction: object):
        return self.exec('verify_authority', signed_transaction)


if __name__ == '__main__':
    s = Steem()
    print(s.get_account_count())
