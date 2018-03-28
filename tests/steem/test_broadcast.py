from steem import Steem
from steem.commit import Commit
from steembase.exceptions import RPCError


def test_claim_reward():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steem=Steem(keys=[wif]))

    try:
        c.claim_reward_balance(account='test')
    except RPCError as e:
        assert 'missing required posting authority' in str(e)
    else:
        raise Exception('expected RPCError')


def test_witness_update():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steem=Steem(keys=[wif]))
    key = 'STM1111111111111111111111111111111114T1Anm'
    props = {
        'account_creation_fee': '0.500 STEEM',
        'maximum_block_size': 65536,
        'sbd_interest_rate': 0}

    try:
        c.witness_update(signing_key=key, account='test', props=props, url='')
    except RPCError as e:
        assert 'missing required active authority' in str(e)
    else:
        raise Exception('expected RPCError')
