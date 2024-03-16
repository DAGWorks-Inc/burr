=================
State Persistence
=================

.. _state-persistence:

Key to writing a real life `burr` application is state persistence. E.g. you're building a chat bot and you
want to store the conversation history and then reload it when you restart. Or, you have a long running process,
or series of agents, and you want to store the state of the process after each action, and then reload it if it fails, etc.

Here we'll walk through how to add state persistence to a `burr` application. The following walk through the relevant
ApplicationBuilder() methods, and then a full toy example.

.initialize_from() method
_________________________
TODO:

.with_persister() method
________________________
TODO:

Supported Persistence Backends
______________________________
TODO:
