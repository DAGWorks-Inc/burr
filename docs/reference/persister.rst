=================
State Persistence
=================

Burr provides a set of tools to make loading and saving state easy. These are functions
that will be used by lifecycle hooks to save and load state.

If you want to implement your own state persister (to bridge it with a database), you should implement
the ``BaseStatePersister`` interface.

.. autoclass:: burr.core.persistence.BaseStatePersister
   :members:
   :show-inheritance:
   :inherited-members:

   .. automethod:: __init__

Internally, this interface combines the following two interfaces:

.. autoclass:: burr.core.persistence.BaseStateLoader
   :members:

   .. automethod:: __init__

.. autoclass:: burr.core.persistence.BaseStateSaver
    :members:
    :show-inheritance:
    :inherited-members:

    .. automethod:: __init__


Supported Implementations
=========================

.. _persistersref:

Currently we support the following, although we highly recommend you contribute your own! We will be adding more shortly.

.. autoclass:: burr.core.persistence.SQLLitePersister
   :members:

   .. automethod:: __init__


.. autoclass:: burr.integrations.persisters.postgresql.PostgreSQLPersister
   :members:

   .. automethod:: __init__


.. autoclass:: burr.integrations.persisters.b_redis.RedisPersister
   :members:

   .. automethod:: __init__

.. autoclass:: burr.integrations.persisters.b_mongodb.MongoDBPersister
   :members:
   .. automethod:: __init__


Note that the :py:class:`LocalTrackingClient <burr.tracking.client.LocalTrackingClient>` leverages the :py:class:`BaseStateLoader <burr.core.persistence.BaseStateLoader>` to allow loading state,
although it uses different mechanisms to save state (as it tracks more than just state).
