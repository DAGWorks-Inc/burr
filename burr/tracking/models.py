import datetime
import inspect
from typing import Any, Dict, Optional

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
        "tracking-client",
    )


class IdentifyingModel(pydantic.BaseModel):
    model_type: str


class ActionModel(IdentifyingModel):
    """Pydantic model that represents an action for storing/visualization in the UI"""

    name: str
    reads: list[str]
    writes: list[str]
    code: str
    model_type: str = "action"

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
    model_type: str = "transition"

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
    model_type: str = "application"

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
    model_type: str = "begin_entry"


class EndEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a step"""

    end_time: datetime.datetime
    action: str
    result: Optional[dict]
    exception: Optional[str]
    state: Dict[str, Any]  # TODO -- consider logging updates to the state so we can recreate
    model_type: str = "end_entry"
