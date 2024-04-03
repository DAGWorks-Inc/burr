=================
State Persistence
=================

.. _state-persistence:

The key to writing a real life ``burr`` application is state persistence. For example, say you're building a chat bot and you
want to store the conversation history and then reload it when you restart. Or, you have a long running process/series of agents,
and you want to store the state of the process after each action, and then reload it if it fails, etc....

``Burr`` provides a few simple interfaces to do this with minimal changes. Let's walk through a simple chatbot example as we're explaining concepts:

State Keys
----------
Burr `applications` are, by defult, keyed on two entities:

1. ``app_uid`` - A unique identifier for the application. This is used to identify the application in the persistence layer.
2. ``partition_key`` - An identifier for grouping (partitioning) applications

In the case of a chatbot, the ``app_uid`` could be a uuid, and the ``partition_key`` could be the user's name.
Note that ``partition_key`` can be `None` if this is not relevant. A UUID is always generated for the ``app_uid`` if not provided.

Initializing state
------------------

To initialize state from a database, you can employ the :py:meth:`initialize_from <burr.core.application.ApplicationBuilder.initialize_from>` method
in the :py:class:`ApplicationBuilder <burr.core.application.ApplicationBuilder>`.

This action takes in an initializer (an implementation of :py:class:`StateInitializer <burr.core.persistence.BaseStateLoader>`) a well as:

- ``resume_at_next_action`` -- a boolean that says whether to start where you left off, or go back to the ``default_entrypoint``.
- ``default_entrypoint`` -- the entry point to start at if ``resume_at_next_action`` is False, or no state is found
- ``default_state`` -- the default state to use if no state is found

Note that you cannot use this in conjunction with :py:meth:`with_state <burr.core.application.ApplicationBuilder.with_state>`
or :py:meth:`with_entrypoint <burr.core.application.ApplicationBuilder.with_entrypoint>` -- these are mutually exclusive.
Either you load from state or you start from scratch.

Writing state
_____________

To write state to a database, you can use the :py:meth:`with_state_persister <burr.core.application.ApplicationBuilder.with_state_persister>` method in the
:py:class:`ApplicationBuilder <burr.core.application.ApplicationBuilder>`. This takes in a persister (an implementation of
:py:class:`StatePersister <burr.core.persistence.BaseStatePersister>`). It writes state to the database after each action.


An example
__________

To make the above more concrete, let's look at a basic chatbot:

.. code-block:: python

    state_persister =  SQLLitePersister(db_path=".sqllite.db", table_name="table")
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
        .initialize(
            initializer=state_persister,
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
