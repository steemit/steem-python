from steem.account import Account


def test_history():
    ah = Account('barbara2')
    hist1 = [x['index'] for x in list(ah.history())]
    hist2 = [x['index'] for x in list(ah.history_reverse())]

    # pprint(list(zip(h1, h2[::-1])))

    # various tests of equality should pass
    assert len(hist1) == len(hist2)
    assert set(hist1) == set(hist2) == set(range(ah.virtual_op_count() + 1))
    assert hist1 == hist2[::-1] == list(range(ah.virtual_op_count() + 1))
