from steem.steemd import Steemd
from steem.commit import Commit
from steembase.exceptions import RPCError


def test_transfer():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steemd_instance=Steemd(nodes=[]),
               keys=[wif])

    rpc_error = None
    try:
        c.transfer('test2', '1.000', 'STEEM', 'foo', 'test')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'tx_missing_active_auth' in rpc_error


def test_claim_reward():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steemd_instance=Steemd(nodes=[]),
               keys=[wif])

    rpc_error = None
    try:
        c.claim_reward_balance(
            account='test',
            reward_steem='1.000 STEEM',
            reward_vests='0.000000 VESTS',
            reward_sbd='0.000 SBD')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'tx_missing_posting_auth' in rpc_error


def test_witness_update():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steemd_instance=Steemd(nodes=[]),
               keys=[wif])

    signing_key = 'STM1111111111111111111111111111111114T1Anm'
    props = {
        'account_creation_fee': '0.500 STEEM',
        'maximum_block_size': 65536,
        'sbd_interest_rate': 0}

    rpc_error = None
    try:
        c.witness_update(
            signing_key=signing_key,
            account='test',
            props=props,
            url='foo')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'tx_missing_active_auth' in rpc_error


def test_witness_set_properties():
    wif = '5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3'
    c = Commit(steemd_instance=Steemd(nodes=[]),
               keys=[wif])

    signing_key = 'STM1111111111111111111111111111111114T1Anm'
    props = [
        ['account_creation_fee', 'd0070000000000000354455354530000'],
        ['key', ('032d2a4af3e23294e0a1d9dbc46e0272d'
                 '8e1977ce2ae3349527cc90fe1cc9c5db9')]
    ]

    rpc_error = None
    try:
        c.witness_set_properties(
            signing_key=signing_key,
            props=props,
            account='test')
    except RPCError as e:
        rpc_error = str(e)
    else:
        raise Exception('expected RPCError')

    assert 'tx_missing_other_auth' in rpc_error
