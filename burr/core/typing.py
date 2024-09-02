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
