# Official Python STEEM Library

`steem-python` is the official Steem library for Python. It comes with a
BIP38 encrypted wallet and a practical CLI utility called `steempy`.

Currently only python3 is supported.  Python2 support is planned.

# Installation

## Easy installation with pip3

```
pip3 install --user steem
```

You can also use pipenv:

## Or you can use Pipenv, the new hotness

```
git clone https://github.com/steemit/steem-python.git
cd steem-python
pipenv install --three --dev
pipenv install .
```

# CLI tools

The library comes with a few console scripts.

* `steempy`:
    * rudimentary blockchain CLI (needs some TLC)
* `steemtail`:
    * useful for e.g. `steemtail -f -j | jq --unbuffered --sort-keys .`

# Documentation

Documentation is available at **http://steem.readthedocs.io**

# TODO

* fix parts that were copied from python-graphenelib that only support
  python3 to support python2 as well
* more unit-tests
* 100% documentation coverage
* migrate to click CLI library

# Notice

This library is *under development*.  Beware.
