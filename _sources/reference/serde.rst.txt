==================================
Serialization & Deserialization
==================================

Burr provides a set of tools to make loading and saving state easy. These are functions
that will be used by lifecycle hooks to save and load state.

If you want to implement your own serialization and deserialization, you should implement
the ``serialize`` & ``deserialize`` functions, which act as an interface. ``serialize`` uses
singledispatch and operates on a Type level. While ``deserialize`` registers a string value
to a function.

.. automodule:: burr.core.serde
   :members:

Each serialize function needs to a mirror deserialize function. To know which
deserialize function to use, the serialize function needs to return a dictionary and have
``burr.core.serde.KEY`` as one of the keys mapping to the appropriate value.
This is used to identify the deserialization function to use.

Out of the box Implementations
==============================

.. _serderef:

The following implementations are available assuming you have the right dependencies in your environment:

LangChain Objects
^^^^^^^^^^^^^^^^^

.. automodule:: burr.integrations.serde.langchain
   :members:

Pandas Objects
^^^^^^^^^^^^^^^^^

.. automodule:: burr.integrations.serde.pandas
   :members:

Pickle-able Objects
^^^^^^^^^^^^^^^^^^^

.. automodule:: burr.integrations.serde.pickle
   :members:

Pydantic Objects
^^^^^^^^^^^^^^^^^

.. automodule:: burr.integrations.serde.pydantic
   :members:
