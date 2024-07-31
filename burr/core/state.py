import abc
import copy
import dataclasses
import importlib
import inspect
import logging
from typing import Any, Callable, Dict, Iterator, Mapping, Union

from burr.core import serde

logger = logging.getLogger(__name__)

FIELD_SERIALIZATION = {}


def register_field_serde(field_name: str, serializer: Callable, deserializer: Callable):
    """Registers a custom serializer + deserializer for a field globally.

    This is useful for really controlling how a field is serialized and deserialized for
    tracking / persistence.

    .. code-block:: python

        def my_field_serializer(value: MyType, **kwargs) -> dict:
            serde_value = _do_something_to_serialize(value)
            return {"value": serde_value}

        def my_field_deserializer(value: dict, **kwargs) -> MyType:
            serde_value = value["value"]
            return _do_something_to_deserialize(serde_value)

        register_field_serde("my_field", my_field_serializer, my_field_deserializer)

    :param field_name: The name of the field to register the serializer for.
    :param serializer: A function that takes the field value and returns a JSON serializable object.
    :param deserializer: A function that takes the JSON serializable object and returns the field value.
    """
    # assert that the serializer has **kwargs argument; it also needs to return a dict but we can't check that.
    # def name(value: Any, **kwargs) -> dict
    serializer_sig = inspect.signature(serializer)
    if not any(param.kind == param.VAR_KEYWORD for param in serializer_sig.parameters.values()):
        raise ValueError(f"Serializer for [{field_name}] must have **kwargs argument.")

    # assert that the deserializer has **kwargs argument; it also needs to return a dict but we can't check that.
    deserializer_sig = inspect.signature(deserializer)
    if not any(param.kind == param.VAR_KEYWORD for param in deserializer_sig.parameters.values()):
        raise ValueError(f"Deserializer for [{field_name}] must have **kwargs argument.")

    FIELD_SERIALIZATION[field_name] = (serializer, deserializer)


class StateDelta(abc.ABC):
    """Represents a delta operation for state. This represents a transaction.
    Note it has the ability to mutate state in-place, but will be layered behind an immutable
    state object."""

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Unique name of this operation for ser/deser"""
        pass

    def serialize(self) -> dict:
        """Converts the state delta to a JSON object"""
        if not dataclasses.is_dataclass(self):
            raise TypeError("serialize method is only supported for dataclass instances")
        return dataclasses.asdict(self)

    def base_serialize(self) -> dict:
        """Converts the state delta to a JSON object"""
        return {"name": self.name(), "operation": self.serialize()}

    def validate(self, input_state: Dict[str, Any]):
        """Validates the input state given the state delta. This is a no-op by default, as most operations are valid"""
        pass

    @classmethod
    def deserialize(cls, json_dict: dict) -> "StateDelta":
        """Converts a JSON object to a state delta"""
        if not dataclasses.is_dataclass(cls):
            raise TypeError("deserialize method is only supported for dataclass types")
        return cls(**json_dict)  # Assumes all fields in the dataclass match keys in json_dict

    def base_deserialize(self, json_dict: dict) -> "StateDelta":
        """Converts a JSON object to a state delta"""
        return self.deserialize(json_dict)

    @abc.abstractmethod
    def reads(self) -> list[str]:
        """Returns the keys that this state delta reads"""
        pass

    @abc.abstractmethod
    def writes(self) -> list[str]:
        """Returns the keys that this state delta writes"""
        pass

    @abc.abstractmethod
    def deletes(self) -> list[str]:
        """Returns the keys that this state delta deletes"""
        pass

    @abc.abstractmethod
    def apply_mutate(self, inputs: dict):
        """Applies the state delta to the inputs"""
        pass


@dataclasses.dataclass
class SetFields(StateDelta):
    """State delta that sets fields in the state"""

    values: Mapping[str, Any]

    @classmethod
    def name(cls) -> str:
        return "set"

    def reads(self) -> list[str]:
        return list(self.values.keys())

    def writes(self) -> list[str]:
        return list(self.values.keys())

    def deletes(self) -> list[str]:
        return []

    def apply_mutate(self, inputs: dict):
        inputs.update(self.values)


@dataclasses.dataclass
class AppendFields(StateDelta):
    """State delta that appends to fields in the state"""

    values: Mapping[str, Any]

    @classmethod
    def name(cls) -> str:
        return "append"

    def reads(self) -> list[str]:
        return list(self.values.keys())

    def writes(self) -> list[str]:
        return list(self.values.keys())

    def deletes(self) -> list[str]:
        return []

    def apply_mutate(self, inputs: dict):
        for key, value in self.values.items():
            if key not in inputs:
                inputs[key] = []
            if not isinstance(inputs[key], list):
                raise ValueError(f"Cannot append to non-list value {key}={inputs[self.key]}")
            inputs[key] = [
                *inputs[key],
                value,
            ]  # Not as efficient but safer, so we don't mutate the original list
            # we're doing this to avoid a copy.deepcopy() call, so it is already more efficient than it was before
            # That said, if one modifies prior values in the list, it is on them, and undefined behavior

    def validate(self, input_state: Dict[str, Any]):
        incorrect_types = {}
        for write_key in self.writes():
            if write_key in input_state and not hasattr(input_state[write_key], "append"):
                incorrect_types[write_key] = type(input_state[write_key])
        if incorrect_types:
            raise ValueError(
                f"Cannot append to non-appendable values: {incorrect_types}. "
                f"Please ensure that all fields are list-like."
            )


@dataclasses.dataclass
class IncrementFields(StateDelta):
    values: Mapping[str, int]

    @classmethod
    def name(cls) -> str:
        return "increment"

    def reads(self) -> list[str]:
        return list(self.values.keys())

    def writes(self) -> list[str]:
        return list(self.values.keys())

    def deletes(self) -> list[str]:
        return []

    def validate(self, input_state: Dict[str, Any]):
        incorrect_types = {}
        for write_key in self.writes():
            if write_key in input_state and not isinstance(input_state[write_key], int):
                incorrect_types[write_key] = type(input_state[write_key])
        if incorrect_types:
            raise ValueError(
                f"Cannot increment non-integer values: {incorrect_types}. "
                f"Please ensure that all fields are integers."
            )

    def apply_mutate(self, inputs: dict):
        for key, value in self.values.items():
            if key not in inputs:
                inputs[key] = value
            else:
                inputs[key] += value


@dataclasses.dataclass
class DeleteField(StateDelta):
    """State delta that deletes fields from the state"""

    keys: list[str]

    @classmethod
    def name(cls) -> str:
        return "delete"

    def reads(self) -> list[str]:
        return []

    def writes(self) -> list[str]:
        return []

    def deletes(self) -> list[str]:
        return list(self.keys)

    def apply_mutate(self, inputs: dict):
        for key in self.keys:
            inputs.pop(key, None)


class State(Mapping):
    """An immutable state object. This is the only way to interact with state in Burr."""

    def __init__(self, initial_values: Dict[str, Any] = None):
        if initial_values is None:
            initial_values = dict()
        self._state = initial_values

    def apply_operation(self, operation: StateDelta) -> "State":
        """Applies a given operation to the state, returning a new state"""
        new_state = copy.copy(self._state)  # TODO -- restrict to just the read keys
        operation.validate(new_state)
        operation.apply_mutate(
            new_state
        )  # todo -- validate that the write keys are the only different ones
        # we want to carry this on for now
        return State(new_state)

    def get_all(self) -> Dict[str, Any]:
        """Returns the entire state, realize as a dictionary. This is a copy."""
        return dict(self)

    def serialize(self, **kwargs) -> dict:
        """Converts the state to a JSON serializable object"""
        _dict = self.get_all()

        def _serialize(k, v, **extrakwargs) -> Union[dict, str]:
            """chooses the correct serde function for the given key and calls it"""
            if k in FIELD_SERIALIZATION:
                result = FIELD_SERIALIZATION[k][0](v, **extrakwargs)
                if not isinstance(result, dict):
                    raise ValueError(
                        f"Field serde for {k} must return a dict,"
                        f" but {FIELD_SERIALIZATION[k][0].__name__} returned {type(result)} ({str(result)[0:10]})."
                    )
                return result
            return serde.serialize(v, **extrakwargs)

        return {k: _serialize(k, v, **kwargs) for k, v in _dict.items()}

    @classmethod
    def deserialize(cls, json_dict: dict, **kwargs) -> "State":
        """Converts a dictionary representing a JSON object back into a state"""

        def _deserialize(k, v: Union[str, dict], **extrakwargs) -> Callable:
            """chooses the correct serde function for the given key and calls it"""
            if k in FIELD_SERIALIZATION:
                return FIELD_SERIALIZATION[k][1](v, **extrakwargs)
            return serde.deserialize(v, **extrakwargs)

        return State({k: _deserialize(k, v, **kwargs) for k, v in json_dict.items()})

    def update(self, **updates: Any) -> "State":
        """Updates the state with a set of key-value pairs
        Does an upsert operation (if the keys exist their value will be overwritten,
        otherwise they will be created)

        .. code-block:: python

            state = State({"a": 1})
            state.update(a=2, b=3)  # State({"a": 2, "b": 3})

        :param updates: Updates to apply
        :return: A new state with the updates applied
        """
        return self.apply_operation(SetFields(updates))

    def append(self, **updates: Any) -> "State":
        """Appends to the state with a set of key-value pairs. Each one
        must correspond to a list-like object, or an error will be raised.

        This is an upsert operation, meaning that if the key does not
        exist, a new list will be created with the value in it.

        .. code-block:: python

            state = State({"a": [1]})
            state.append(a=2)  # State({"a": [1, 2]})

        :param updates: updates to apply
        :return: new state object
        """

        return self.apply_operation(AppendFields(updates))

    def increment(self, **updates: int) -> "State":
        """Increments the state with a set of key-value pairs. Each one
        must correspond to an integer, or an error will be raised.

        :param updates: updates to apply
        :return: new state object
        """ ""
        return self.apply_operation(IncrementFields(updates))

    def wipe(self, delete: list[str] = None, keep: list[str] = None):
        """Wipes the state, either by deleting the keys in delete and keeping everything else
         or keeping the keys in keep. and deleting everything else. If you pass nothing in
         it will delete the whole thing.

        :param delete: Keys to delete
        :param keep: Keys to keep
        :return: A new state object
        """
        if delete is not None and keep is not None:
            raise ValueError(
                f"You cannot specify both delete and keep -- not both! "
                f"You have specified: delete={delete}, keep={keep}"
            )
        if delete is not None:
            fields_to_delete = delete
        else:
            fields_to_delete = [key for key in self._state if key not in keep]
        return self.apply_operation(DeleteField(fields_to_delete))

    def merge(self, other: "State") -> "State":
        """Merges two states together, overwriting the values in self
        with those in other."""
        return State({**self.get_all(), **other.get_all()})

    def subset(self, *keys: str, ignore_missing: bool = True) -> "State":
        """Returns a subset of the state, with only the given keys"""
        return State(
            {key: self[key] for key in keys if key in self or not ignore_missing},
        )

    def __getitem__(self, __k: str) -> Any:
        return self._state[__k]

    def __len__(self) -> int:
        return len(self._state)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._state)

    def __repr__(self):
        return self.get_all().__repr__()  # quick hack


# We register the serde plugins here that we'll automatically try to load.
# In the future if we need to reorder/replace, we'll just have some
# check here that can skip loading plugins/override which ones to load.
# Note for pickle, we require people to manually register the type for that.
for serde_plugin in ["langchain", "pydantic", "pandas"]:
    try:
        importlib.import_module(f"burr.integrations.serde.{serde_plugin}")
    except ImportError:
        logger.debug(f"Skipped registering {serde_plugin} serde plugin.")
