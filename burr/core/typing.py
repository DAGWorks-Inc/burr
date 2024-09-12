from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Generic, Type, TypeVar

BaseType = TypeVar("BaseType")
# SpecificType = TypeVar('SpecificType', bound=BaseType)

if TYPE_CHECKING:
    from burr.core import Action, Graph, State

try:
    from typing import Self
except ImportError:
    Self = "TypingSystem"


class TypingSystem(abc.ABC, Generic[BaseType]):
    @abc.abstractmethod
    def state_type(self) -> Type[BaseType]:
        """Gives the type that represents the state of the
        application at any given time. Note that this must have
        adequate support for Optionals (E.G. non-required values).

        :return:
        """

    @abc.abstractmethod
    def state_pre_action_run_type(self, action: Action, graph: Graph) -> Type[BaseType]:
        """Gives the type that represents the state after an action has completed.
        Note that this could be smart -- E.g. it should have all possible upstream
        types filled in.

        :param action:
        :return:
        """

    @abc.abstractmethod
    def state_post_action_run_type(self, action: Action, graph: Graph) -> Type[BaseType]:
        """Gives the type that represents the state after an action has completed.
        Note that this could be smart -- E.g. it should have all possible upstream
        types filled in.

        :param action:
        :return:
        """

    def validate_state(self, state: State) -> None:
        """Validates the state to ensure it is valid.

        :param state:
        :return:
        """

    @abc.abstractmethod
    def construct_data(self, state: State[BaseType]) -> BaseType:
        """Constructs a type based on the arguments passed in.

        :param kwargs:
        :return:
        """

    @abc.abstractmethod
    def construct_state(self, data: BaseType) -> State[BaseType]:
        """Constructs a state based on the arguments passed in.

        :param kwargs:
        :return:
        """


StateInputType = TypeVar("StateInputType")
StateOutputType = TypeVar("StateOutputType")
IntermediateResultType = TypeVar("IntermediateResultType")


class ActionSchema(
    abc.ABC,
    Generic[
        StateInputType,
        StateOutputType,
        IntermediateResultType,
    ],
):
    """Quick wrapper class to represent a schema. Note that this is currently used internally,
    just to store the appropriate information. This does not validate or do conversion, currently that
    is done within the pydantic model state typing system (which is also internal in its implementation).



    We will likely centralize that logic at some point when we get more -- it would look something like this:
    1. Action is passed an ActionSchema
    2. Action is parameterized on the ActionSchema types
    3. Action takes state, validates the type and converts to StateInputType
    4. Action runs, returns intermediate result + state
    5. Action validates intermediate result type (or converts to dict? Probably just keeps it
    6. Action converts StateOutputType to State
    """

    @abc.abstractmethod
    def state_input_type() -> Type[StateInputType]:
        pass

    @abc.abstractmethod
    def state_output_type() -> Type[StateOutputType]:
        pass

    @abc.abstractmethod
    def intermediate_result_type() -> Type[IntermediateResultType]:
        pass


class DictBasedTypingSystem(TypingSystem[dict]):
    """Effectively a no-op. State is backed by a dictionary, which allows every state item
    to... be a dictionary."""

    def state_type(self) -> Type[dict]:
        return dict

    def state_pre_action_run_type(self, action: Action, graph: Graph) -> Type[dict]:
        return dict

    def state_post_action_run_type(self, action: Action, graph: Graph) -> Type[dict]:
        return dict

    def construct_data(self, state: State[dict]) -> dict:
        return state.get_all()

    def construct_state(self, data: dict) -> State[dict]:
        return State(data, typing_system=self)
