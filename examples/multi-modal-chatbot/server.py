import functools
import importlib
from typing import List, Literal

import pydantic
from fastapi import APIRouter

from burr.core import Application, ApplicationBuilder
from burr.tracking import LocalTrackingClient

"""This file represents a simple chatbot API backed with Burr.
We manage an application, write to it with post endpoints, and read with
get/ endpoints.

This demonstrates how you can build interactive web applications with Burr!
"""
# We're doing dynamic import cause this lives within examples/ (and that module has dashes)
# navigate to the examples directory to read more about this!
chat_application = importlib.import_module(
    "burr.examples.multi-modal-chatbot.application"
)  # noqa: F401

# the app is commented out as we include the router.
# app = FastAPI()

router = APIRouter()

graph = chat_application.base_graph


class ChatItem(pydantic.BaseModel):
    """Pydantic model for a chat item. This is used to render the chat history."""

    content: str
    type: Literal["image", "text", "code", "error"]
    role: Literal["user", "assistant"]


@functools.lru_cache(maxsize=128)
def _get_application(project_id: str, app_id: str) -> Application:
    """Quick tool to get the application -- caches it"""
    tracker = LocalTrackingClient(project=project_id, storage_dir="~/.burr")
    return (
        ApplicationBuilder()
        .with_graph(graph)
        # initializes from the tracking log if it does not already exist
        .initialize_from(
            tracker,
            resume_at_next_action=False,  # always resume from entrypoint in the case of failure
            default_state={"chat_history": []},
            default_entrypoint="prompt",
        )
        .with_tracker(tracker)
        .with_identifiers(app_id=app_id)
        .build()
    )


@router.post("/response/{{project_id}}/{{app_id}}", response_model=List[ChatItem])
def chat_response(project_id: str, app_id: str, prompt: str) -> List[ChatItem]:
    """Chat response endpoint. User passes in a prompt and the system returns the
    full chat history, so its easier to render.

    :param project_id: Project ID to run
    :param app_id: Application ID to run
    :param prompt: Prompt to send to the chatbot
    :return:
    """
    burr_app = _get_application(project_id, app_id)
    _, _, state = burr_app.run(halt_after=["response"], inputs=dict(prompt=prompt))
    return state.get("chat_history", [])


@router.get("/response/{project_id}/{app_id}", response_model=List[ChatItem])
def chat_history(project_id: str, app_id: str) -> List[ChatItem]:
    """Endpoint to get chat history. Gets the application and returns the chat history from state.

    :param project_id: Project ID
    :param app_id: App ID.
    :return: The list of chat items in the state
    """
    chat_app = _get_application(project_id, app_id)
    state = chat_app.state
    return state.get("chat_history", [])


@router.post("/create/{project_id}/{app_id}", response_model=str)
async def create_new_application(project_id: str, app_id: str) -> str:
    """Endpoint to create a new application -- used by the FE when
    the user types in a new App ID

    :param project_id: Project ID
    :param app_id: App ID
    :return: The app ID
    """
    # side-effect of this persists it -- see the application function for details
    _get_application(app_id=app_id, project_id=project_id)
    return app_id  # just return it for now


# comment this back in fro a standalone chatbot API
# app.include_router(router, prefix="/api/v0/chatbot")
