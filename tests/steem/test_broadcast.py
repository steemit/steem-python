from steem import Steem
from steem.commit import Commit
from steembase.exceptions import RPCError


def test_claim_reward():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steem=Steem(keys=[wif]))

    rpc_error = None
    try:
        c.claim_reward_balance(account='test')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'missing required posting authority' in rpc_error


def test_witness_update():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steem=Steem(keys=[wif]))
    key = 'STM1111111111111111111111111111111114T1Anm'
    props = {
        'account_creation_fee': '0.500 STEEM',
        'maximum_block_size': 65536,
        'sbd_interest_rate': 0}

    rpc_error = None
    try:
        c.witness_update(signing_key=key, account='test', props=props, url='')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'missing required active authority' in rpc_error
