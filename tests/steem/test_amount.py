from steem.amount import Amount


def test_amount_init():
    a = Amount('1 STEEM')
    assert dict(a) == {'amount': 1.0, 'asset': 'STEEM'}
