from funcy.colls import pluck
from steem.steemd import Steemd

from steem import Steem


def test_get_version():
    """ We should be able to call get_version on steemd """
    s = Steemd()
    response = s.call('get_version', api='login_api')
    version = response['blockchain_version']
    assert version[0:4] == '0.19'


def test_ensured_block_ranges():
    """ Post should load correctly if passed a dict or string identifier. """
    s = Steemd()
    assert list(pluck('block_num', s.get_blocks_range(1000, 2000))) == list(
        range(1000, 2000))

    # for fuzzing in s.get_block_range_ensured() use:
    # degraded_results = [x for x in results if x['block_num'] %
    #     random.choice(range(1, 10)) != 0]
