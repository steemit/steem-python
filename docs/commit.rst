Commit - Tools for committing actions on STEEM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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