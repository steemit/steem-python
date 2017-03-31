from steem.account import Account


def test_history():
    a = Account('barbara2')
    h1 = [x['index'] for x in list(a.history())]
    h2 = [x['index'] for x in list(a.history_reverse())]

    # pprint(list(zip(h1, h2[::-1])))

    # various tests of equality should pass
    assert len(h1) == len(h2)
    assert set(h1) == set(h2) == set(range(a.virtual_op_count() + 1))
    assert h1 == h2[::-1] == list(range(a.virtual_op_count() + 1))
