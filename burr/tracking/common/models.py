import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from burr.common import types as burr_types
from burr.core import Action
from burr.core.application import ApplicationGraph
from burr.core.graph import Transition
from burr.integrations.base import require_plugin

try:
    import pydantic
except ImportError as e:
    require_plugin(
        e,
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
    inputs: List[str] = pydantic.Field(default_factory=list)
    optional_inputs: List[str] = pydantic.Field(default_factory=list)

    @staticmethod
    def from_action(action: Action) -> "ActionModel":
        """Creates an ActionModel from an action.

        :param action: Action to create the model from
        :return:
        """
        code = action.get_source()  # delegate to the action
        optional_inputs, required_inputs = action.optional_and_required_inputs
        return ActionModel(
            name=action.name,
            reads=list(action.reads),
            writes=list(action.writes),
            code=code,
            inputs=list(required_inputs),
            optional_inputs=list(optional_inputs),
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


class PointerModel(IdentifyingModel):
    """Stores pointers to unique identifiers for an application.
    This is used by a few different places to, say, store parent references
    bewteen application instances.
    """

    app_id: str
    sequence_id: Optional[int]
    partition_key: Optional[str]
    type: str = "pointer_data"

    @staticmethod
    def from_pointer(pointer: Optional[burr_types.ParentPointer]) -> Optional["PointerModel"]:
        return (
            PointerModel(
                app_id=pointer.app_id,
                sequence_id=pointer.sequence_id,
                partition_key=pointer.partition_key,
            )
            if pointer is not None
            else None
        )


class ChildApplicationModel(IdentifyingModel):
    """Stores data about a child application (either a fork or a spawned application).
    This allows us to link from parent -> child in the UI."""

    child: PointerModel
    event_time: datetime.datetime
    event_type: Literal[
        "fork", "spawn_start"
    ]  # TODO -- get spawn_end working when we have interaction hooks (E.G. on app fn calls)
    sequence_id: Optional[int]
    type: str = "child_application_data"


class ApplicationModel(IdentifyingModel):
    """Pydantic model that represents an application for storing/visualization in the UI"""

    entrypoint: str
    actions: list[ActionModel]
    transitions: list[TransitionModel]
    type: str = "application"

    @staticmethod
    def from_application_graph(
        application_graph: ApplicationGraph,
    ) -> "ApplicationModel":
        return ApplicationModel(
            entrypoint=application_graph.entrypoint.name,
            actions=[ActionModel.from_action(action) for action in application_graph.actions],
            transitions=[
                TransitionModel.from_transition(transition)
                for transition in application_graph.transitions
            ],
        )


class ApplicationMetadataModel(IdentifyingModel):
    """Pydantic model that represents metadata for an application.
    We will want to add tags here when we have them."""

    partition_key: Optional[str] = None
    parent_pointer: Optional[PointerModel] = None  # pointer to parent data
    spawning_parent_pointer: Optional[PointerModel] = None  # pointer to spawning parent data
    type: str = "application_metadata"


INPUT_FILTERLIST = {"__tracer", "__context"}


def _filter_inputs(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in INPUT_FILTERLIST}


class BeginEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the beginning of a step"""

    start_time: datetime.datetime
    action: str
    inputs: Dict[str, Any]
    sequence_id: int
    type: str = "begin_entry"


class EndEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a step"""

    end_time: datetime.datetime
    action: str
    result: Optional[dict]
    exception: Optional[str]
    state: Dict[str, Any]  # TODO -- consider logging updates to the state so we can recreate
    sequence_id: int
    type: str = "end_entry"


class BeginSpanModel(IdentifyingModel):
    """Pydantic model that represents an entry for the beginning of a span"""

    start_time: datetime.datetime
    action_sequence_id: int
    span_id: str  # unique among the application
    span_name: str
    parent_span_id: Optional[str]
    span_dependencies: list[str]
    type: str = "begin_span"

    @property
    def sequence_id(self) -> int:
        return self.action_sequence_id


class EndSpanModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a span"""

    end_time: datetime.datetime
    action_sequence_id: int
    span_id: str  # unique among the application
    type: str = "end_span"

    @property
    def sequence_id(self) -> int:
        return self.action_sequence_id


class AttributeModel(IdentifyingModel):
    """Represents a logged artifact"""

    key: str
    action_sequence_id: int
    span_id: Optional[
        str
    ]  # It doesn't have to relate to a span, it can be at the level of an action as well
    value: Union[dict, str, int, float, bool, list, None]
    tags: Dict[str, str]
    type: str = "attribute"
