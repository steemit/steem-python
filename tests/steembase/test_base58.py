import unittest
import re
from steembase.base58 import (Base58, base58decode, base58encode,
                              base58CheckEncode, base58CheckDecode,
                              gphBase58CheckEncode, gphBase58CheckDecode)


class Testcases(unittest.TestCase):
    def test_base58decode(self):
        self.assertEqual([
            base58decode(
                '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'),
            base58decode(
                '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss'),
            base58decode('5KfazyjBBtR2YeHjNqX5D6MXvqTUd2iZmWusrdDSUqoykTyWQZB')
        ], [
            '800c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e'
            '19d72aa1d507a5b8d',
            '80e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991'
            'b7852b8555c5bbb26',
            '80f3a375e00cc5147f30bee97bb5d54b31a12eee148a1ac31ac9edc4e'
            'cd13bc1f80cc8148e'
        ])

    def test_base58encode(self):
        self.assertEqual([
            '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ',
            '5KYZdUEo39z3FPrtuX2QbbwGnNP5zTd7yyr2SC1j299sBCnWjss',
            '5KfazyjBBtR2YeHjNqX5D6MXvqTUd2iZmWusrdDSUqoykTyWQZB'
        ], [
            base58encode('800c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe47'
                         '1be89827e19d72aa1d507a5b8d'),
            base58encode('80e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b93'
                         '4ca495991b7852b8555c5bbb26'),
            base58encode('80f3a375e00cc5147f30bee97bb5d54b31a12eee148a1ac3'
                         '1ac9edc4ecd13bc1f80cc8148e')
        ])

    def test_gphBase58CheckEncode(self):
        self.assertEqual([
            gphBase58CheckEncode(
                "02e649f63f8e8121345fd7f47d0d185a3ccaa843115cd2e9"
                "392dcd9b82263bc680"),
            gphBase58CheckEncode(
                "021c7359cd885c0e319924d97e3980206ad64387aff54908"
                "241125b3a88b55ca16"),
            gphBase58CheckEncode(
                "02f561e0b57a552df3fa1df2d87a906b7a9fc33a83d5d15f"
                "a68a644ecb0806b49a"),
            gphBase58CheckEncode(
                "03e7595c3e6b58f907bee951dc29796f3757307e700ecf3d"
                "09307a0cc4a564eba3")
        ], [
            "6dumtt9swxCqwdPZBGXh9YmHoEjFFnNfwHaTqRbQTghGAY2gRz",
            "5725vivYpuFWbeyTifZ5KevnHyqXCi5hwHbNU9cYz1FHbFXCxX",
            "6kZKHSuxqAwdCYsMvwTcipoTsNE2jmEUNBQufGYywpniBKXWZK",
            "8b82mpnH8YX1E9RHnU2a2YgLTZ8ooevEGP9N15c1yFqhoBvJur"
        ])

    def test_gphBase58CheckDecode(self):
        self.assertEqual([
            "02e649f63f8e8121345fd7f47d0d185a3ccaa84311"
            "5cd2e9392dcd9b82263bc680",
            "021c7359cd885c0e319924d97e3980206ad64387af"
            "f54908241125b3a88b55ca16",
            "02f561e0b57a552df3fa1df2d87a906b7a9fc33a83"
            "d5d15fa68a644ecb0806b49a",
            "03e7595c3e6b58f907bee951dc29796f3757307e70"
            "0ecf3d09307a0cc4a564eba3",
        ], [
            gphBase58CheckDecode(
                "6dumtt9swxCqwdPZBGXh9YmHoEjFFnNfwHaTqRbQTghGAY2gRz"),
            gphBase58CheckDecode(
                "5725vivYpuFWbeyTifZ5KevnHyqXCi5hwHbNU9cYz1FHbFXCxX"),
            gphBase58CheckDecode(
                "6kZKHSuxqAwdCYsMvwTcipoTsNE2jmEUNBQufGYywpniBKXWZK"),
            gphBase58CheckDecode(
                "8b82mpnH8YX1E9RHnU2a2YgLTZ8ooevEGP9N15c1yFqhoBvJur")
        ])

    def test_btsb58(self):
        ml = """
        02e649f63f8e8121345fd7f47d0d185a3ccaa843115cd2e9392dcd9b82263bc680
        03457298c4b2c56a8d572c051ca3109dabfe360beb144738180d6c964068ea3e58
        021c7359cd885c0e319924d97e3980206ad64387aff54908241125b3a88b55ca16
        02f561e0b57a552df3fa1df2d87a906b7a9fc33a83d5d15fa68a644ecb0806b49a
        03e7595c3e6b58f907bee951dc29796f3757307e700ecf3d09307a0cc4a564eba3"""

        for x in re.split('\s+', ml):
            self.assertEqual(x, gphBase58CheckDecode(gphBase58CheckEncode(x)))

    def test_Base58CheckDecode(self):
        self.assertEqual([
            "02e649f63f8e8121345fd7f47d0d185a3ccaa84"
            "3115cd2e9392dcd9b82263bc680",
            "021c7359cd885c0e319924d97e3980206ad6438"
            "7aff54908241125b3a88b55ca16",
            "02f561e0b57a552df3fa1df2d87a906b7a9fc33"
            "a83d5d15fa68a644ecb0806b49a",
            "03e7595c3e6b58f907bee951dc29796f3757307"
            "e700ecf3d09307a0cc4a564eba3",
            "02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda86507661901adb49",
            "5b921f7051be5e13e177a0253229903c40493df410ae04f4a450c85568f19131",
            "0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e74ec00e",
            "6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855d919d3e",
            "b84abd64d66ee1dd614230ebbe9d9c6d66d78d93927c395196666762e9ad69d8"
        ], [
            base58CheckDecode(
                "KwKM6S22ZZDYw5dxBFhaRyFtcuWjaoxqDDfyCcBYSevnjdfm9Cjo"),
            base58CheckDecode(
                "KwHpCk3sLE6VykHymAEyTMRznQ1Uh5ukvFfyDWpGToT7Hf5jzrie"),
            base58CheckDecode(
                "KwKTjyQbKe6mfrtsf4TFMtqAf5as5bSp526s341PQEQvq5ZzEo5W"),
            base58CheckDecode(
                "KwMJJgtyBxQ9FEvUCzJmvr8tXxB3zNWhkn14mWMCTGSMt5GwGLgz"),
            base58CheckDecode(
                "5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd"),
            base58CheckDecode(
                "5JWcdkhL3w4RkVPcZMdJsjos22yB5cSkPExerktvKnRNZR5gx1S"),
            base58CheckDecode(
                "5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq"),
            base58CheckDecode(
                "5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R"),
            base58CheckDecode(
                "5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7")
        ])

    def test_base58CheckEncodeDecode(self):
        ml = """
            02e649f63f8e8121345fd7f47d0d185a3ccaa843115cd2e9392dcd9b82263bc680
            03457298c4b2c56a8d572c051ca3109dabfe360beb144738180d6c964068ea3e58
            021c7359cd885c0e319924d97e3980206ad64387aff54908241125b3a88b55ca16
            02f561e0b57a552df3fa1df2d87a906b7a9fc33a83d5d15fa68a644ecb0806b49a
            03e7595c3e6b58f907bee951dc29796f3757307e700ecf3d09307a0cc4a564eba3
        """

        for x in re.split('\s+', ml):
            self.assertEqual(x, base58CheckDecode(base58CheckEncode(0x80, x)))

    def test_Base58(self):
        self.assertEqual([
            format(
                Base58(
                    "02b52e04a0acfe611a4b6963462aca94b6ae02b24e321eda865076619"
                    "01adb49"), "wif"),
            format(
                Base58(
                    "5b921f7051be5e13e177a0253229903c40493df410ae04f4a450c8556"
                    "8f19131"), "wif"),
            format(
                Base58(
                    "0e1bfc9024d1f55a7855dc690e45b2e089d2d825a4671a3c3c7e4ea4e"
                    "74ec00e"), "wif"),
            format(
                Base58(
                    "6e5cc4653d46e690c709ed9e0570a2c75a286ad7c1bc69a648aae6855"
                    "d919d3e"), "wif"),
            format(
                Base58(
                    "b84abd64d66ee1dd614230ebbe9d9c6d66d78d93927c395196666762e"
                    "9ad69d8"), "wif")
        ], [
            "5HqUkGuo62BfcJU5vNhTXKJRXuUi9QSE6jp8C3uBJ2BVHtB8WSd",
            "5JWcdkhL3w4RkVPcZMdJsjos22yB5cSkPExerktvKnRNZR5gx1S",
            "5HvVz6XMx84aC5KaaBbwYrRLvWE46cH6zVnv4827SBPLorg76oq",
            "5Jete5oFNjjk3aUMkKuxgAXsp7ZyhgJbYNiNjHLvq5xzXkiqw7R",
            "5KDT58ksNsVKjYShG4Ls5ZtredybSxzmKec8juj7CojZj6LPRF7"
        ])


if __name__ == '__main__':
    unittest.main()
