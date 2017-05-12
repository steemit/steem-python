Transactions and Accounts
~~~~~~~~~~~~~~~~~~~~~~~~~

Commit
======

The Commit class contains helper methods for `posting, voting, transferring funds, updating witnesses` and more.
You don't have to use this class directly, all of its methods are accessible trough main ``Steem`` class.

.. code-block:: python

   # accessing commit methods trough Steem
   s = Steem()
   s.commit.transfer(...)

   # is same as
   c = Commit(steem=Steem())
   c.transfer(..)

.. autoclass:: steem.steem.Commit
   :members:

--------


TransactionBuilder
==================

.. autoclass:: steem.transactionbuilder.TransactionBuilder
   :members:

--------

Wallet
======

Wallet is a low-level utility.
It could be used to create 3rd party cli and GUI wallets on top of ``steem-python``'s infrastructure.

.. automodule:: steem.wallet
   :members:
