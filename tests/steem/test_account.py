import unittest
from steem.account import Account

testaccount = "xeroc"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(Testcases, self).__init__(*args, **kwargs)
        self.account = Account(testaccount)

    def test_readAccount(self):
        self.assertEqual(self.account["id"], 1489)

    def test_getbalance(self):
        self.account.get_balances()


if __name__ == '__main__':
    unittest.main()
