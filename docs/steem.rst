Steem - Your Starting Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quick Start
-----------
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

Importing your Steem Account
============================
`steem-python` comes with a BIP38 encrypted wallet, which holds your private keys.



Alternatively, you can also pass required WIF's to ``Steem()`` initializer.

::

    from steem import Steem
    s = Steem(keys=['<private_posting_key>', '<private_active_key>'])

Using the encrypted wallet is however a recommended way.

Please check :doc:`cli` to learn how to set up the wallet.

Interfacing with steemd
=======================
``Steem()`` inherits API methods from ``Steemd``, which can be called like so:

.. code-block:: python

   s = Steem()

   s.get_account('ned')
   s.get_block(8888888)
   s.get_content('author', 'permlink')
   s.broadcast_transaction(...)
   # and many more

You can see the list of available methods by calling ``help(Steem)``.
If a method is not available trough the Python API, we can call it manually using ``s.exec()``:

.. code-block:: python

   s = Steem()

   # this call
   s.get_followers('furion', 'abit', 'blog', 10)

   # is same as
   s.exec('get_followers',
          'furion', 'abit', 'blog', 10,
           api='follow_api')

Commit and Wallet
=================
``Steem()`` comes equipped with ``Commit`` and ``Wallet``, accessible via dot-notation.

.. code-block:: python

   s = Steem()

   # accessing Commit methods
   s.commit.transfer(...)

   # accessing Wallet methods
   s.wallet.get_active_key_for_account(...)

Please check :doc:`core` documentation to learn more.


Steem
-----

As displayed in the `Quick Start` above, ``Steem`` is the main class of this library. It acts as a gateway to other components, such as
``Steemd``, ``Commit``, ``Wallet`` and ``HttpClient``.

Any arguments passed to ``Steem`` as ``kwargs`` will naturally flow to sub-components. For example, if we initialize
Steem with ``steem = Steem(no_broadcast=True)``, the ``Commit`` instance is configured to not broadcast any transactions.
This is very useful for testing.

.. autoclass:: steem.steem.Steem
   :members:


Steemd API
----------

Steemd contains API generating utilities. ``Steemd``'s methods will be automatically available to ``Steem()`` classes.
See :doc:`steem`.

.. _steemd-reference:

.. automodule:: steem.steemd
   :members:
