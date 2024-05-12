from functools import singledispatch
from typing import Any, Union

KEY = "__burr_serde__"


class StringDispatch:
    """Class to capture how to deserialize something.

    We register a key with a deserializer function. It's like single dispatch
    but based on a string key value.

    Example usage:

    .. code-block:: python

        from burr.core import serde

        @serde.deserializer.register("pickle")
        def deserialize_pickle(value: dict, pickle_kwargs: dict = None, **kwargs) -> cls:
            if pickle_kwargs is None:
                pickle_kwargs = {}
            return pickle.loads(value["value"], **pickle_kwargs)

    What this does is register the function `deserialize_pickle` with the key "pickle".
    This should mirror the appropriate serialization function - which is what sets the key value
    to match the deserializer function against.

    Notice that this namespaces its kwargs. This is important because we don't want to have
    a collision with other kwargs that might be passed in.
    """

    def __init__(self):
        self.func_map = {}

    def register(self, key):
        def decorator(func):
            self.func_map[key] = func
            return func

        return decorator

    def call(self, key, *args, **kwargs):
        if key in self.func_map:
            return self.func_map[key](*args, **kwargs)
        else:
            raise ValueError(f"No function registered for key: {key}")


deserializer = StringDispatch()


def deserialize(value: Any, **kwargs) -> Any:
    """Main function to deserialize a value.

    Looks for a key in the value if it's a dictionary and calls the appropriate deserializer function.
    """
    if isinstance(value, dict):
        class_to_instantiate = value.get(KEY, None)
        if class_to_instantiate is not None:
            return deserializer.call(class_to_instantiate, value, **kwargs)
        else:
            return {k: deserialize(v, **kwargs) for k, v in value.items()}
    elif isinstance(value, list):
        return [deserialize(v, **kwargs) for v in value]
    else:
        return value


@singledispatch
def serialize(value, **kwargs) -> Any:
    """This is the default implementation for serializing a value.

    All other implementations should be registered with the `@serialize.register` decorator.

    Each function should output a dictionary, and include the `KEY` & value to use for deserialization.

    :param value: The value to serialize
    :param kwargs: Any additional keyword arguments. Each implementation should namespace their kwargs.
    :return: A dictionary representation of the value
    """
    if value is None:
        return None
    return str(value)


@serialize.register(str)
@serialize.register(int)
@serialize.register(float)
@serialize.register(bool)
def serialize_primitive(value, **kwargs) -> Union[str, int, float, bool]:
    return value


@serialize.register(dict)
def serialize_dict(value: dict, **kwargs) -> dict[str, Any]:
    return {k: serialize(v, **kwargs) for k, v in value.items()}


@serialize.register(list)
def serialize_list(value: list, **kwargs) -> list[Any]:
    return [serialize(v, **kwargs) for v in value]
