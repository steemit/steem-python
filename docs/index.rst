Welcome to steem-python
=======================

``steem-python`` is the official STEEM library for Python.
It can be used to interface with the STEEM blockchain.


Quick Start
-----------

To install the library, simply run:

::

   pip install -U steem

You can start using the library with just a few lines of code, as seen in this quick example:

.. code-block:: python

   # first, we initialize Steem class
   from steem import Steem
   s = Steem()

.. code-block:: python

   # check @ned's balance
   >>> s.get_account('ned')['sbd_balance']
   '980.211 SBD'

   # lets send $1.0 SBD to @ned
   >>> s.commit.transfer(to='ned', amount=1, asset='SBD', account='furion')
   {'expiration': '2017-03-12T17:54:43',
    'extensions': [],
    'operations': [['transfer',
      {'amount': '1.000 SBD', 'from': 'furion', 'memo': '', 'to': 'ned'}]],
    'ref_block_num': 23008,
    'ref_block_prefix': 961695589,
    'signatures': ['1f1322be9ca0c22b27c0385c929c9863901ac78cdaedea2162024ea040e22c4f8b542c02d96cbc761cbe4a188a932bc715bb7bcaf823b6739a44bb29fa85f96d2f']}

   # yup, its there
   >>> s.get_account('ned')['sbd_balance']
   '981.211 SBD'

Getting Started
---------------
.. toctree::
   :maxdepth: 1

   install
   tutorial



Digging Deeper
--------------
.. toctree::
   :maxdepth: 2

   steem
   steemd
   commit
   convenience

Low Level
---------
.. toctree::
   :maxdepth: 1

   http_client
   steembase

Other
-----

* :ref:`genindex`
