# Official Python STEEM Library

`steem-python` is the official Steem library for Python. It comes with a
BIP38 encrypted wallet and a practical CLI utility called `steempy`.

This library works on both Python 2.7 and 3.6.

# Installation

## Installation with pipenv (recommended)

Install pipenv first if you don't have it:

`pip3 install --upgrade --user pipenv`

Then, install steem-python using it:

```
git clone https://github.com/steemit/steem-python.git
cd steem-python
pipenv install --three --dev        # use --two instead of --three for Python 2.7
pipenv install .
```

## Installation with pip3

```
git clone https://github.com/steemit/steem-python.git
cd steem-python
pip3 install --user .
```

Note that installation using `pip3` requires that the `pipenv` module be installed to parse the requirements out of the `Pipfile` so that pip3 can do the install.  If you get an error about `pipenv` not being found, you can resolve it with a `pip3 install --upgrade --user pipenv`, then the install with `pip3` will work as usual.

## Homebrew Build Prereqs

If you're on a mac, you may need to do the following first:

```
brew install openssl
export CFLAGS="-I$(brew --prefix openssl)/include $CFLAGS"
export LDFLAGS="-L$(brew --prefix openssl)/lib $LDFLAGS"
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

* more unit tests
* 100% documentation coverage, consistent documentation
* migrate to click CLI library

# Notice

This library is *under development*.  Beware.
