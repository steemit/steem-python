from steem.account import Account


def test_history():
    # TODO 1: test is disabled because api.steemit.com account history
    #         pruning is temporarily in place, breaking assumptions.
    # TODO 2: in addition, the current pruning implementation fails
    #         to remove the very first operation, revealing a bug in
    #         history_reverse() which causes it to be included once
    #         on every page, causing an item count mismatch.
    return

    a = Account('barbara2')
    h1 = [x['index'] for x in list(a.history())]
    h2 = [x['index'] for x in list(a.history_reverse())]

    # pprint(list(zip(h1, h2[::-1])))

    # various tests of equality should pass
    assert len(h1) == len(h2)
    assert set(h1) == set(h2) == set(range(a.virtual_op_count() + 1))
    assert h1 == h2[::-1] == list(range(a.virtual_op_count() + 1))
