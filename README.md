# Official Python STEEM Library

`steem-python` is the official Steem library for Python. It comes with a
BIP38 encrypted wallet and a practical CLI utility called `steempy`.

Currently only python3 is supported.  Python2 support is planned.

# Installation

## Installation with pipenv (recommended)

Install pipenv first if you don't have it:

`pip3 install --upgrade --user pipenv`

Then, install steem-python using it:

```
git clone https://github.com/steemit/steem-python.git
cd steem-python
pipenv install --three --dev
pipenv install .
```

## Installation with pip3

```
git clone https://github.com/steemit/steem-python.git
cd steem-python
pip3 install --user .
```

# CLI tools bundled

The library comes with a few console scripts.

* `steempy`:
    * rudimentary blockchain CLI (needs some TLC and more TLAs)
* `steemtail`:
    * useful for e.g. `steemtail -f -j | jq --unbuffered --sort-keys .`

# Documentation

Documentation is available at **http://steem.readthedocs.io**

# Tests

Some tests are included.  They can be run via either docker or vagrant,
for reproducibility, e.g.:

* `docker build .`

or

* `vagrant up`

# TODO

* fix parts that were copied from python-graphenelib that only support
  python3 to support python2 as well
* more unit tests
* 100% documentation coverage, consistent documentation
* migrate to click CLI library

# Notice

This library is *under development*.  Beware.
