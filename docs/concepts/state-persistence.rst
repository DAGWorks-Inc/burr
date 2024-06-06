=================
State Persistence
=================

.. _state-persistence:

.. note::

    Burr comes with a core set of APIs that enable state `persistence` -- the ability
    to save and load state automatically from a database. This enables you to launch an application,
    pause it, and restart where you left off. The API is customizable, and works with any database you want.

TL;DR
-----

Burr provides an API to save and load state from a database. This enables you to pause and restart applications where you left off.
You can implement a custom state persister or use one of the pre-built ones. You can fork state from a previous run to enable debugging/loading.


Persisting State
----------------

The key to writing a real life ``burr`` application is state persistence. For example, say you're building a chat bot and you
want to store the conversation history and then reload it when you restart. Or, you have a long running process/series of agents,
and you want to store the state of the process after each action, and then reload it if it fails, etc....

``Burr`` provides a few simple interfaces to do this with minimal changes. Let's walk through a simple chatbot example as we're explaining concepts:

State Keys
----------
Burr `applications` are, by default, keyed on two entities:

1. ``app_uid`` - A unique identifier for the application. This is used to identify the application in the persistence layer.
2. ``partition_key`` - An identifier for grouping (partitioning) applications

In the case of a chatbot, the ``app_uid`` could be a uuid, and the ``partition_key`` could be the user's name.
Note that ``partition_key`` can be `None` if this is not relevant. A UUID is always generated for the ``app_uid`` if not provided.

You set these values using the :py:meth:`with_identifiers() <burr.core.application.ApplicationBuilder.with_identifiers>` method.

Initializing state
------------------

To initialize state from a database, you can employ the :py:meth:`initialize_from <burr.core.application.ApplicationBuilder.initialize_from>` method
in the :py:class:`ApplicationBuilder <burr.core.application.ApplicationBuilder>`. Important API note: unless `fork_from_app_id` is specified
below, the values used to query for state are taken from the values provided to :py:meth:`with_identifiers() <burr.core.application.ApplicationBuilder.with_identifiers>`.

This action takes in an initializer (an implementation of :py:class:`StateInitializer <burr.core.persistence.BaseStateLoader>`) a well as:

- ``resume_at_next_action`` -- a boolean that says whether to start where you left off, or go back to the ``default_entrypoint``.
- ``default_entrypoint`` -- the entry point to start at if ``resume_at_next_action`` is False, or no state is found
- ``default_state`` -- the default state to use if no state is found
- ``fork_from_app_id`` -- Optional. A prior app_id to fork state from. This is useful if you want to start from a previous application's state.
- ``fork_from_partition_key`` -- Optional. The partition key to fork from. Goes with ``fork_from_app_id``.
- ``fork_from_sequence_id`` -- Optional. The sequence_id to fork from. Goes with ``fork_from_app_id``.


Note (1): that you cannot use this in conjunction with :py:meth:`with_state <burr.core.application.ApplicationBuilder.with_state>`
or :py:meth:`with_entrypoint <burr.core.application.ApplicationBuilder.with_entrypoint>` -- these are mutually exclusive. If you're
switching to use state persistence, all you need to do is remove the ``with_state`` and ``with_entrypoint`` calls and replace them with
the default state and entrypoint in the ``initialize_from`` call.

Note (2): The loader will not error if no state is found, it will use the default state in this case.

Forking State
_____________
When loading you can also fork state from a previous application. This is useful if you want to start from a previous application's state,
but don't want to add to it. The ``fork_from_app_id`` and ``fork_from_partition_key`` are used to identify the application to fork from, while
``fork_from_sequence_id`` is used to identify the sequence_id to use. This is useful if you want to fork from a specific point in the application,
rather than the latest state. This is especially useful for debugging, or building an application that enables you
to rewind state and make different choices.

When you use the ``fork_from_app_id`` to load state, the values passed to :py:meth:`with_identifiers() <burr.core.application.ApplicationBuilder.with_identifiers>`
will then dictate where the new application state is ultimately stored.

For a quick overview of using it, Ashis from `PeanutRobotics <https://peanutrobotics.com>`_ has kindly submitted a
video on how they use this feature:

.. raw:: html

    <iframe width="800" height="455" src="https://www.youtube.com/embed/98vxhIcE6NI?si=w1vMHr9QUxjlVVgm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


Writing state
_____________

To write state to a database, you can use the :py:meth:`with_state_persister <burr.core.application.ApplicationBuilder.with_state_persister>` method in the
:py:class:`ApplicationBuilder <burr.core.application.ApplicationBuilder>`. This takes in a persister (an implementation of
:py:class:`StatePersister <burr.core.persistence.BaseStatePersister>`). It writes state to the database after each action.


An example
__________

To make the above more concrete, let's look at a basic chatbot:

.. code-block:: python

    state_persister =  SQLLitePersister(db_path=".sqllite.db", table_name="burr_state")
    app = (
        ApplicationBuilder()
        .with_actions(
            ai_converse=ai_converse,
            human_converse=human_converse,
            terminal=burr.core.Result("chat_history"),
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .initialize_from(
            state_persister,
            resume_at_next_action=True,
            default_state={"chat_history" : []},
            default_entrypoint="human_converse
        )
        .with_state_persister(state_persister)
        .with_identifiers(app_id=app_id)
        .build()
    )

In this case, we both read and write using the ``SQLLitePersistor``. Note that this is the most common case.
However, if you want to just read (E.G. for debugging), or you want to just write (if you're always creating a new app),
you can leave out ``initialize`` or ``with_state_persister`` respectively.



Supported Persistence Backends
______________________________
See :ref:`available persisters here <persistersref>`.
Note that the tracker also allows reloading from a file, but this is not recommended for production use.


Customizing State Persistence
-----------------------------

Burr exposes the :py:class:`BaseStatePersister <burr.core.persistence.BaseStatePersister>` API for custom state persistence. Implement,
pass into the above functions, and you can write to whatever database you want! Please contribute back to the community if you do so.


Loading from the Tracker
------------------------

You can use the tracking feature additionally as a persister. This enables you to load from prior
tracked runs. This is useful for debugging, or building an application that enables you to rewind state and make different choices.

.. code-block:: python

    tracker = LocalTrackingClient(project=project_name)
    app = (
        ApplicationBuilder()
        .with_actions(
            ai_converse=ai_converse,
            human_converse=human_converse,
            terminal=burr.core.Result("chat_history"),
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .initialize_from(
            tracker,
            resume_at_next_action=True,
            default_state={"chat_history" : []},
            default_entrypoint="human_converse
        )
        .with_tracker(tracker)
        .with_identifiers(app_id=app_id)
        .build()
    )

In this case the ``LocalTrackingClient`` is used both as a persister and a loader. It will persist as it is
running (by tracking), and then load from the tracker if the application is restarted. This is useful for local development.

Custom Serialization and Deserialization
----------------------------------------
See :doc:`serde` for more information on how to customize state serialization and deserialization.

This includes how to register custom serializers and deserializers based on type, as well
as :ref:`registering custom serializers and deserializers for a field<state-field-serialization>` in state.
