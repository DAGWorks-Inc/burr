import abc
import copy
import dataclasses
import logging
from typing import Any, Dict, Iterator, Mapping

logger = logging.getLogger(__name__)


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

    def apply_mutate(self, inputs: dict):
        for key, value in self.values.items():
            if key not in inputs:
                inputs[key] = []
            if not isinstance(inputs[key], list):
                raise ValueError(f"Cannot append to non-list value {key}={inputs[self.key]}")
            inputs[key].append(value)

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
class DeleteField(StateDelta):
    """State delta that deletes fields from the state"""

    keys: list[str]

    @classmethod
    def name(cls) -> str:
        return "delete"

    def reads(self) -> list[str]:
        return list(self.keys)

    def writes(self) -> list[str]:
        return []

    def apply_mutate(self, inputs: dict):
        for key in self.keys:
            inputs.pop(key, None)


class State(Mapping):
    """An immutable state object. Things to consider:
    1. Adding hooks on change
    2. Pulling/pushing to external places
    3. Simultaneous writes/reads in the case of parallelism
    4. Schema enforcement -- how to specify/manage? Should this be a
    dataclass when implemented?
    """

    def __init__(self, initial_values: Dict[str, Any] = None):
        if initial_values is None:
            initial_values = dict()
        self._state = initial_values

    def apply_operation(self, operation: StateDelta) -> "State":
        """Applies a given operation to the state, returning a new state"""
        new_state = copy.deepcopy(self._state)  # TODO -- restrict to just the read keys
        operation.validate(new_state)
        operation.apply_mutate(
            new_state
        )  # todo -- validate that the write keys are the only different ones
        return State(new_state)

    def get_all(self) -> Dict[str, Any]:
        """Returns the entire state, realize as a dictionary. This is a copy."""
        return dict(self)

    def update(self, **updates: Any) -> "State":
        """Updates the state with a set of key-value pairs"""
        return self.apply_operation(SetFields(updates))

    def append(self, **updates: Any) -> "State":
        """For each pair specified, appends to a list in state."""

        return self.apply_operation(AppendFields(updates))

    def wipe(self, delete: list[str] = None, keep: list[str] = None):
        """Wipes the state, either by deleting the keys in delete and keeping everything else
         or keeping the keys in keep. and deleting everything else. If you pass nothing in
         it will delete the whole thing.

        :param delete:
        :param keep:
        :return:
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
        return State({key: self[key] for key in keys if key in self or not ignore_missing})

    def __getitem__(self, __k: str) -> Any:
        return self._state[__k]

    def __len__(self) -> int:
        return len(self._state)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._state)

    def __repr__(self):
        return self.get_all().__repr__()  # quick hack
