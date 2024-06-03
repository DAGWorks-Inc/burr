================================
Serialization / Deserialization
================================

Core to :ref:`state-persistence <state-persistence>` is the ability to serialize and deserialize objects.

Burr comes with a pluggable serialization/deserialization mechanism.

Currently it is class/type based. Field level serialization is in the works! See :py:func:`serialize <burr.core.serde.serialize>` and :py:func:`deserialize <burr.core.serde.deserialize>` for reference details.

How it works
____________
The :py:class:`State <burr.core.state.State>` object has a :py:meth:`serialize <burr.core.state.State.serialize>` method that returns a dictionary.
The :py:class:`State <burr.core.state.State>` class also has a :py:meth:`deserialize <burr.core.state.State.deserialize>` method that takes a dictionary and returns a state object.

It is then delegated to persisters and trackers to call these methods and store the serialized state.

Underneath the State object delegates to the :py:func:`serialize <burr.core.serde.serialize>` and :py:func:`deserialize <burr.core.serde.deserialize>` functions.

How to create your own serialization/deserialization
_____________________________________________________
To create your own serialization/deserialization mechanism, you need to implement the following code. The assumption
here is that you have some custom class you want to serialize/deserialize.

.. code-block:: python

    from typing import Any, Dict
    from burr.core import serde

    class MY_CLASS:
        # your custom class/type
        pass

    @serde.serialize.register(MY_CLASS)
    def serialize_myclass(value: cls, myclass_kwargs: dict = None, **kwargs) -> dict:
        """Serializes the value using my custom methodology.

        :param value: the value to serialize.
        :param myclass_kwargs: not required. Optional.
        :param kwargs:
        :return: dictionary of serde.KEY and value
        """
        if myclass_kwargs is None:
            myclass_kwargs = {}
        return {
            # required to identify how to deserialize
            serde.KEY: "myclass",
            # delegate to your custom serialization
            "value": some_custom_serialization(value, **myclass_kwargs),
        }

    @serde.deserializer.register("myclass")
    def deserialize_myclass(value: dict, myclass_kwargs: dict = None, **kwargs) -> cls:
        """Deserializes the value using my custom methodology.

        :param value: the value to deserialize from.
        :param myclass_kwargs: not required. Optional.
        :param kwargs:
        :return: object of type cls
        """
        if myclass_kwargs is None:
            myclass_kwargs = {}
        # delegate to your custom deserialization
        return some_custom_deserialization(value["value"], **myclass_kwargs)

You'll need to this code to run/be imported so it can register itself.

Field level Serialization/Deserialization
_________________________________________

.. _state-field-serialization:

Field level serialization/deserialization is handled by a registration function in the state module.
Fields will be first checked to see if there is a custom serializer/deserializer registered for that field,
before delegating to the default serialization/deserialization mechanism.

.. code-block:: python

        from burr.core import state

        def my_field_serializer(value: MyType, **kwargs) -> dict:
            serde_value = _do_something_to_serialize(value)
            return {"value": serde_value}

        def my_field_deserializer(value: dict, **kwargs) -> MyType:
            serde_value = value["value"]
            return _do_something_to_deserialize(serde_value)

        state.register_field_serde("my_field", my_field_serializer, my_field_deserializer)

This will register a custom serializer/deserializer for the field "my_field".

Requirements for the serializer/deserializer functions:

    1. The serializer function needs to return a dictionary.
    2. Both function signatures needs to have a ``**kwargs`` parameter to allow for custom arguments to be passed in. We advise namespacing the kwargs provided to avoid conflicts with other serializers/deserializers.
