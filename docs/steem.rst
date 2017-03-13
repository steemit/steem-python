Steem - Your Starting Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Steem library has been designed to allow developers to easily access its routines and make use of the network without dealing with all the releated blockchain technology and cryptography. This library can be used to do anything that is allowed according to the Steem blockchain protocol.


Interfacing with steemd
-----------------------
``Steem()`` inherits API methods from ``Steemd()``, which can be called like so:

.. code-block:: python

   s = Steem()

   s.get_account('ned')
   s.get_block(8888888)
   s.get_content('author', 'permlink')
   s.broadcast_transaction(...)
   # and many more

You can see the list of available methods by calling ``help(Steem)`` or in :doc:`steemd`.
If a method is not available in the Python API, we can call it manually using ``s.exec()``:

.. code-block:: python

   s = Steem()

   # this call
   s.get_followers('furion', 'abit', 'blog', 10)

   # is same as
   s.exec('get_followers',
          'furion', 'abit', 'blog', 10,
           api='follow_api')

Commit and Wallet
-----------------
``Steem()`` comes equipped with ``Commit`` and ``Wallet``, accessible via dot-notation.

.. code-block:: python

   s = Steem()

   # accessing Commit methods
   s.commit.transfer(...)

   # accessing Wallet methods
   s.wallet.get_active_key_for_account(...)

.. autoclass:: steem.steem.Steem
   :members: