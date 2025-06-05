import dataclasses
import functools
from typing import Any, Callable, Dict, List, Literal, Optional, Type, TypeVar

import pydantic
from fastapi import APIRouter, Request
from pydantic import BaseModel

from burr.core.application import Application, ApplicationBuilder
from burr.core.graph import Graph
from burr.core.persistence import BaseStatePersister, SQLLitePersister
from burr.integrations.pydantic import PydanticTypingSystem, model_to_dict

import examples.fastapi.application as email_assistant_application

# current_directory = os.path.dirname(os.path.abspath(__file__))

# # Remove the current directory from sys.path
# if current_directory in sys.path:
#     sys.path.remove(current_directory)

# # Import the Pydantic library
# import pydantic
# import fastapi

# # Add the current directory back to sys.path
# sys.path.insert(0, current_directory)


AppStateT = TypeVar("AppStateT", bound=pydantic.BaseModel)


class BurrFastAPIConfig(BaseModel):
    terminating_actions: List[str]  # list of actions after which to terminate
    requires_input: List[str]
    fixed_inputs: Optional[dict] = None  # Fixed inputs to use for all requests
    hide_state_fields: Optional[List[str]] = None  # Fields to hide from the state
    require_partition_keys: bool = False  # Require partition keys for all requests
    graph: Graph  # partially built builder -- no uids or other keys yet
    persister: BaseStatePersister  # persister so we can handle storage
    state_type: Type[pydantic.BaseModel]  # state type
    default_model: Optional[pydantic.BaseModel] = None
    entrypoint: str

    class Config:
        arbitrary_types_allowed = True

    # TODO -- expose tracking + hooks

    # This must be partially built (no uids or anything)


@functools.lru_cache(maxsize=1000)  # TODO -- determine how to do this in a cleaner way
def _get_or_create(
    application_id: str, partition_key: Optional[str], config: BurrFastAPIConfig
) -> Application:
    return (
        ApplicationBuilder()
        .with_graph(config.graph)
        .with_state_persister(config.persister)
        .with_identifiers(app_id=application_id, partition_key=partition_key)
        .with_typing(PydanticTypingSystem(config.state_type))
        .initialize_from(
            initializer=config.persister,
            resume_at_next_action=True,
            default_state=model_to_dict(config.default_model) if config.default_model else {},
            default_entrypoint=config.entrypoint,
        )
        .build()
    )


async def _run_through(
    app_id: Optional[str], partition_key: str, inputs: Dict[str, Any], config: BurrFastAPIConfig
):
    """This advances the state machine, moving through to the next 'halting' point"""
    app = _get_or_create(app_id, partition_key)
    await app.arun(  # Using this as a side-effect, we'll just get the state aft
        halt_before=config.requires_input,  # TODO -- ensure that it's not None
        halt_after=config.terminating_actions,
        inputs=inputs,
    )
    return app.state.data, app.get_next_action()


@dataclasses.dataclass
class Endpoint:
    path: List[str]  # "/do/something/{application_id}/{partition_key}"
    method: Literal["GET", "POST"]
    body_type: Optional[Type[pydantic.BaseModel]]
    response_type: Type[pydantic.BaseModel]
    template: Literal["input", "get_or_create"]
    config: BurrFastAPIConfig
    internal_version: int = 0

    def get_endpoint_handler(self) -> Callable:
        """Gives the endpoint handler for this endpoint to be registered by FastAPI.
        Returns a function that FastAPI can parse.

        :return: _description_
        """
        PartitionKeyType = str if self.config.require_partition_keys else Optional[str]

        async def get_or_create_handler(
            request: Request, application_id: str, partition_key: PartitionKeyType
        ):
            app = _get_or_create(application_id, partition_key, self.config)
            next_action = app.get_next_action()
            return self.response_type(
                state=app.state.data,
                next_action=next_action.name if next_action is not None else None,
                app_id=app.uid,
            )

        async def input_handler(
            request: Request, application_id, partition_key: PartitionKeyType, body: self.body_type
        ):
            # TODO -- implement me!
            state_output, next_action = await _run_through(
                application_id, partition_key, body.dict(), self.config
            )
            # TODO -- ensure this is of the same base-class, we're kind of hardcoding it
            return self.response_type(
                state=state_output,
                next_action=next_action.name if next_action else None,
                app_id=application_id,
            )

        if self.template == "input":
            return input_handler
        elif self.template == "get_or_create":
            return get_or_create_handler


def _create_input_endpoint(action_name: str, config: BurrFastAPIConfig) -> Endpoint:
    """Creates an endpoint for user-required data

    :param burr_app: Application to create endpoint for
    :param action_name: Name of the action that that endpoint will *start* at
    :param fixed_inputs: Fixed inputs -- these can be used by the endpoint
    :return: Endpoint object that will be used to generate a FastAPI app
    """
    action = config.graph.get_action(action_name)
    if action is None:
        raise ValueError(f"Action {action_name} not found in graph")
    # Schema for action
    required_inputs, optional_inputs = action.input_schema  # each Dict[str, type]
    # TODO -- create a pydantic model dynamically that has:
    # 1. the required inputs as the field "inputs", minus any that are in the variable "fixed_inputs" (hidden)
    # 2. the optional inputs in the field "inputs", with default to null + optional, minus any that are in the field "fixed_inputs" (hidden)
    filtered_required = {
        k: (v, ...) for k, v in required_inputs.items() if k not in (config.fixed_inputs or {})
    }
    filtered_optional = {
        k: (Optional[v], None) for k, v in optional_inputs.items() if (config.fixed_inputs or {})
    }

    # Combine filtered required and optional fields
    inputs_fields = {**filtered_required, **filtered_optional}

    import pprint

    pprint.pprint(inputs_fields)
    # Dynamically create the Inputs model
    InputsModel = pydantic.create_model("InputsModel", **inputs_fields)
    ResponseModel = pydantic.create_model(
        "ResponseModel",
        state=(config.state_type, ...),
        next_action=(Optional[str], ...),
        app_id=(str, ...),
    )
    return Endpoint(
        path=[f"/{action_name}/{{application_id}}/{{partition_key}}"],
        method="POST",
        body_type=InputsModel,
        response_type=ResponseModel,
        template="input",
        config=config,
    )


def _create_get_or_create_endpoint(name: str, config: BurrFastAPIConfig) -> Endpoint:
    return Endpoint(
        path=[f"/{name}/{{application_id}}/{{partition_key}}"],
        method="POST",
        body_type=None,
        response_type=config.state_type,
        template="get_or_create",
        config=config,
    )


def _gather_endpoints(config: BurrFastAPIConfig) -> List[Endpoint]:
    actions_with_input = set(config.requires_input or [])
    entrypoint = config.entrypoint
    # terminating_actions = set(config.terminating_actions)

    endpoints = []
    for action in config.graph.actions:
        if action.name in actions_with_input:
            endpoints.append(_create_input_endpoint(action.name, config))
        if action.name == entrypoint:
            endpoints.append(_create_input_endpoint(entrypoint, config))

    endpoints.append(_create_get_or_create_endpoint("get_or_create", config))
    return endpoints


def _register_endpoint(router: APIRouter, endpoint: Endpoint):
    if endpoint.method == "POST":
        router.post(
            "/".join(endpoint.path),
            response_model=endpoint.response_type,
        )(endpoint.get_endpoint_handler())
    elif endpoint.method == "GET":
        router.get(
            "/".join(endpoint.path),
            response_model=endpoint.response_type,
        )(endpoint.get_endpoint_handler())
    # TODO -- handle other types


# def _validate_and_extract_app_type(
#     burr_app: Application[pydantic.BaseModel],
# ) -> Type[pydantic.BaseModel]:
#     typing_system = burr_app.state.typing_system
#     if not isinstance(typing_system, PydanticTypingSystem):
#         raise ValueError(
#             "Burr FastAPI requires a PydanticTypingSystem. Use with_typing(PydanticTypingSystem(MyStateModel(...))) to specify"
#         )
#     return typing_system.state_type()


def _validate_terminating_actions(graph: Graph, terminating_actions: List[str]):
    missing_actions = set(terminating_actions) - {action.name for action in graph.actions}
    if missing_actions:
        raise ValueError(f"Terminating actions {missing_actions} not found in graph")


def _validate_inputs_types(input_types: dict, action_name: str):
    inputs_with_any_type = set()
    for key, value in input_types.items():
        if value is Any:
            inputs_with_any_type.add(key)
    if inputs_with_any_type:
        raise ValueError(
            f"Action {action_name} has inputs with Any type: {inputs_with_any_type}."
            "This means that they are not specified. Please specify by assigning"
            "parameter types in the action definition"
        )


def _validate_require_input_actions(config: BurrFastAPIConfig):
    requires_input_actions = set(config.requires_input or [])
    missing_actions = requires_input_actions - {action.name for action in config.graph.actions}
    if missing_actions:
        raise ValueError(f"Actions {missing_actions} not found in graph")
    burr_actions = {action.name: action for action in config.graph.actions}
    for action_name in requires_input_actions:
        action = burr_actions[action_name]
        required_inputs, optional_inputs = action.input_schema
        _validate_inputs_types(required_inputs, action_name)
        _validate_inputs_types(optional_inputs, action_name)


def _validate_state_hide_fields(config: BurrFastAPIConfig, state_type: Type[pydantic.BaseModel]):
    hidden_fields = set(config.hide_state_fields or [])
    model_fields = set(state_type.model_fields.keys())
    missing_fields = hidden_fields - model_fields
    if missing_fields:
        raise ValueError(
            f"Fields {missing_fields} not found in state model, ",
            "but specified in hide_fields. Please remove from hide_fields or add to state model",
        )


def _validate_config(config: BurrFastAPIConfig):
    app_type = config.state_type
    _validate_terminating_actions(config.graph, config.terminating_actions)
    _validate_require_input_actions(config)
    _validate_state_hide_fields(config, app_type)


def expose(router: APIRouter, config: BurrFastAPIConfig):
    """Exposes a burr app as a fastAPI app

    :param router: _description_
    :param burr_app: _description_
    :param config: _description_
    """
    _validate_config(config)
    endpoints = _gather_endpoints(config)
    for endpoint in endpoints:
        _register_endpoint(router, endpoint)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    # tracker = LocalTrackingClient(project="test_fastapi_autogen")
    config = BurrFastAPIConfig(
        terminating_actions=["final_result"],
        requires_input=["clarify_instructions", "process_feedback"],
        fixed_inputs={},
        hide_state_fields=[],
        require_partition_keys=False,
        graph=email_assistant_application.graph,
        persister=SQLLitePersister(db_path=".sqllite.db", table_name="test1"),
        state_type=email_assistant_application.EmailAssistantState,
        default_model=email_assistant_application.EmailAssistantState(),
        entrypoint="process_input",
    )
    app = FastAPI()
    router = APIRouter(
        prefix="/email_assistant",
    )
    expose(router, config)
    app.include_router(router)
    uvicorn.run(app, host="localhost", port=7245)
