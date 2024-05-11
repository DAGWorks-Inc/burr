import datetime
import inspect
from typing import Any, Dict, List, Optional, Union

from pydantic import field_serializer

from burr.core import Action
from burr.core.action import FunctionBasedAction, FunctionBasedStreamingAction
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

try:
    # try to import to serialize Langchain messages
    from langchain_core import documents as lc_documents
    from langchain_core import load as lc_serde
    from langchain_core import messages as lc_messages
except ImportError:
    lc_messages = None
    lc_documents = None
    lc_serde = None


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

    @staticmethod
    def from_action(action: Action) -> "ActionModel":
        """Creates an ActionModel from an action.

        :param action: Action to create the model from
        :return:
        """
        if isinstance(action, (FunctionBasedAction, FunctionBasedStreamingAction)):
            code = inspect.getsource(action.fn)
        else:
            code = inspect.getsource(action.__class__)
        optional_inputs, required_inputs = action.optional_and_required_inputs
        return ActionModel(
            name=action.name,
            reads=list(action.reads),
            writes=list(action.writes),
            code=code,
            inputs=list(required_inputs | optional_inputs),
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


class ApplicationMetadataModel(IdentifyingModel):
    """Pydantic model that represents metadata for an application.
    We will want to add tags here when we have them."""

    partition_key: Optional[str]
    type: str = "application_metadata"


INPUT_FILTERLIST = {"__tracer"}


def _filter_inputs(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in INPUT_FILTERLIST}


class BeginEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the beginning of a step"""

    start_time: datetime.datetime
    action: str
    inputs: Dict[str, Any]
    sequence_id: int
    type: str = "begin_entry"

    @field_serializer("inputs")
    def serialize_inputs(self, inputs):
        return _serialize_object(_filter_inputs(inputs))


def _serialize_object(d: object) -> Union[dict, list, object, str]:
    if isinstance(d, list):
        return [_serialize_object(x) for x in d]
    elif isinstance(d, dict):
        return {k: _serialize_object(v) for k, v in d.items()}
    elif lc_messages is not None and isinstance(d, lc_messages.BaseMessage):
        return lc_messages.message_to_dict(d)
    elif lc_documents is not None and isinstance(d, lc_documents.Document):
        if d.is_lc_serializable():
            return lc_serde.dumpd(d)
        else:
            # d.page_content  # hack because not all documents are serializable
            return d.page_content
    elif hasattr(d, "to_document"):
        # langchain can have things that look like a document but aren't...
        return _serialize_object(d.to_document())
    elif hasattr(d, "model_dump"):  # generic pydantic object
        return d.model_dump()
    elif hasattr(d, "to_json"):
        return d.to_json()
    return d


class EndEntryModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a step"""

    end_time: datetime.datetime
    action: str
    result: Optional[dict]
    exception: Optional[str]
    state: Dict[str, Any]  # TODO -- consider logging updates to the state so we can recreate
    sequence_id: int
    type: str = "end_entry"

    @field_serializer("result")
    def serialize_result(self, result):
        return _serialize_object(result)

    @field_serializer("state")
    def serialize_state(self, state):
        return _serialize_object(state)


class BeginSpanModel(IdentifyingModel):
    """Pydantic model that represents an entry for the beginning of a span"""

    start_time: datetime.datetime
    action_sequence_id: int
    span_id: str  # unique among the application
    span_name: str
    parent_span_id: Optional[str]
    span_dependencies: list[str]
    type: str = "begin_span"


class EndSpanModel(IdentifyingModel):
    """Pydantic model that represents an entry for the end of a span"""

    end_time: datetime.datetime
    action_sequence_id: int
    span_id: str  # unique among the application
    type: str = "end_span"
