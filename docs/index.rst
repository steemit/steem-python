Welcome to steem-python
=======================

``steem-python`` is the official STEEM library for Python.
It can be used to interface with the STEEM blockchain.


Getting Started
---------------

To install the library, simply run:

::

   pip install -U steem

You can start using the library with just a few lines of code, as seen in this quick example:

.. code-block:: python

   from steem import Steem

   s = Steem()
   s.get_account('ned')['sbd_balance']
   # '977.574 SBD'


First Steps
===========
.. toctree::
   :maxdepth: 1
   :caption: Contents:

   install


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
