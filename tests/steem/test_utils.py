import unittest

from steem.utils import (
    construct_identifier,
    sanitize_permlink,
    derive_permlink,
    resolve_identifier,
    fmt_time,
)


class Testcases(unittest.TestCase):
    def test_constructIdentifier(self):
        self.assertEqual(construct_identifier("A", "B"), "A/B")

    def test_sanitizePermlink(self):
        self.assertEqual(sanitize_permlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(sanitize_permlink("[](){}"), "")

    def test_derivePermlink(self):
        self.assertEqual(derive_permlink("Hello World"), "hello-world")
        self.assertEqual(derive_permlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(derive_permlink("[](){}"), "")

    def test_resolveIdentifier(self):
        self.assertEqual(resolve_identifier("A/B"), ("A", "B"))

    def test_formatTime(self):
        self.assertEqual(fmt_time(1463480746), "20160517t102546")


if __name__ == '__main__':
    unittest.main()
