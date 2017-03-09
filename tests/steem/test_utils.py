import unittest

from steem.helpers import (
    constructIdentifier,
    sanitizePermlink,
    derivePermlink,
    resolveIdentifier,
    formatTime,
)


class Testcases(unittest.TestCase):
    def test_constructIdentifier(self):
        self.assertEqual(constructIdentifier("A", "B"), "@A/B")

    def test_sanitizePermlink(self):
        self.assertEqual(sanitizePermlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(sanitizePermlink("[](){}"), "")

    def test_derivePermlink(self):
        self.assertEqual(derivePermlink("Hello World"), "hello-world")
        self.assertEqual(derivePermlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(derivePermlink("[](){}"), "")

    def test_resolveIdentifier(self):
        self.assertEqual(resolveIdentifier("@A/B"), ("A", "B"))

    def test_yaml_parse_file(self):
        pass

    def test_formatTime(self):
        self.assertEqual(formatTime(1463480746), "20160517t102546")


if __name__ == '__main__':
    unittest.main()
