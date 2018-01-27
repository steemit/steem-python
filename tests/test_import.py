# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# pylint: disable=wrong-import-position
from steem import Steem
from steembase import account


# pylint: disable=unused-import,unused-variable
def test_import():
    _ = Steem()
    _ = account.PasswordKey
