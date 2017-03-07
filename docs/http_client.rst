HttpClient
~~~~~~~~~~

A fast ``urllib3`` based HTTP client that features:

* Connection Pooling
* Concurrent Processing
* Automatic Node Failover

The functionality of ``HttpClient`` is encapsulated by ``Steem`` class. You shouldn't be using ``HttpClient`` directly,
unless you know exactly what you're doing.

.. autoclass:: steem.steem.HttpClient
   :members: