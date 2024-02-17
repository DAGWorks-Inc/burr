import datetime
import inspect
from typing import Any, Dict, Optional, Union

from pydantic import field_serializer

from burr.core import Action
from burr.core.action import FunctionBasedAction
from burr.core.application import ApplicationGraph, Transition
from burr.integrations.base import require_plugin

try:
    import pydantic
except ImportError as e:
    require_plugin(
        e,
        ["pydantic"],
        "tracking",
    )


class IdentifyingModel(pydantic.BaseModel):
    type: str


class ActionModel(IdentifyingModel):
    """Pydantic model that represents an action for storing/visualization in the UI"""

    name: str
    reads: list[str]
    writes: list[str]
    code: str
    type: str = "action"

    @staticmethod
    def from_action(action: Action) -> "ActionModel":
        """Creates an ActionModel from an action.

        :param action: Action to create the model from
        :return:
        """
        if isinstance(action, FunctionBasedAction):
            code = inspect.getsource(action.fn)
        else:
            code = inspect.getsource(action.__class__)
        return ActionModel(
            name=action.name,
            reads=list(action.reads),
            writes=list(action.writes),
            code=code,
        )


class TransitionModel(IdentifyingModel):
    """Pydantic model that represents a transition for storing/visualization in the UI"""

    from_: str
    to: str
    condition: str
    type: str = "transition"

    @staticmethod
    def from_transition(transition: Transition) -> "TransitionModel":
        return TransitionModel(
            from_=transition.from_.name, to=transition.to.name, condition=transition.condition.name
        )


class ApplicationModel(IdentifyingModel):
    """Pydantic model that represents an application for storing/visualization in the UI"""

    entrypoint: str
    actions: list[ActionModel]
    transitions: list[TransitionModel]
    type: str = "application"

    @staticmethod
    def from_application_graph(application_graph: ApplicationGraph) -> "ApplicationModel":
        return ApplicationModel(
            entrypoint=application_graph.entrypoint.name,
            actions=[ActionModel.from_action(action) for action in application_graph.actions],
            transitions=[
                TransitionModel.from_transition(transition)
                for transition in application_graph.transitions
            ],
        )


class BeginEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the beginning of a step"""

    start_time: datetime.datetime
    action: str
    inputs: Dict[str, Any]
    type: str = "begin_entry"


def _serialize_object(d: object) -> Union[dict, list, object]:
    if isinstance(d, list):
        return [_serialize_object(x) for x in d]
    elif isinstance(d, dict):
        return {k: _serialize_object(v) for k, v in d.items()}
    elif hasattr(d, "model_dump"):
        return d.model_dump()
    elif hasattr(d, "to_json"):
        return d.to_json()
    else:
        return d


class EndEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a step"""

    end_time: datetime.datetime
    action: str
    result: Optional[dict]
    exception: Optional[str]
    state: Dict[str, Any]  # TODO -- consider logging updates to the state so we can recreate
    type: str = "end_entry"

    @field_serializer("result")
    def serialize_result(self, result):
        return _serialize_object(result)

    @field_serializer("state")
    def serialize_state(self, state):
        return _serialize_object(state)
