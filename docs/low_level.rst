Low Level
~~~~~~~~~

HttpClient
----------

A fast ``urllib3`` based HTTP client that features:

* Connection Pooling
* Concurrent Processing
* Automatic Node Failover

The functionality of ``HttpClient`` is encapsulated by ``Steem`` class. You shouldn't be using ``HttpClient`` directly,
unless you know exactly what you're doing.

.. autoclass:: steembase.http_client.HttpClient
   :members:

-------------

steembase
---------

SteemBase contains various primitives for building higher level abstractions.
This module should only be used by library developers or people with deep domain knowledge.

**Warning:**
Not all methods are documented. Please see source.

.. image:: https://i.imgur.com/A9urMG9.png

Account
=======

.. automodule:: steembase.account
   :members:

--------

Base58
======

.. automodule:: steembase.base58
   :members:

--------

Bip38
=====

.. automodule:: steembase.bip38
   :members:


--------

Memo
====

.. automodule:: steembase.memo
   :members:


--------

Operations
==========

.. automodule:: steembase.operations
   :members:


--------

Transactions
============

.. automodule:: steembase.transactions
   :members:



--------

Types
=====

.. automodule:: steembase.types
   :members:

--------

Exceptions
==========

.. automodule:: steembase.exceptions
   :members: