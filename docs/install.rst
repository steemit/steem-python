************
Installation
************

`steem-python` requires Python 3.5 or higher. We don't recommend usage of Python that ships with OS.
If you're just looking for a quick and easy cross-platform solution, feel free to install Python 3.x via easy to use
`Anaconda <https://www.continuum.io/downloads>`_ installer.


Afterwards, you can install `steem-python` with `pip`:

::

    $ pip install steem

You can also perform the installation manually using `setup.py`:

::

    $ git clone https://github.com/steemit/steem-python
    $ cd steem-python
    $ make install

Upgrade
#######

::

   $ pip install -U steem



Namespace Collision
===================

If you have used a piston stack before v0.5, please remove it before installing official version of ``python-steem``.

::

   curl https://raw.githubusercontent.com/steemit/steem-python/master/scripts/nuke_legacy.sh | sh
