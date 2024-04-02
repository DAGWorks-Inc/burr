import functools
import importlib
from typing import List, Literal

import pydantic
from fastapi import APIRouter

from burr.core import Application

"""This file represents a simple chatbot API backed with Burr.
We manage an application, write to it with post endpoints, and read with
get/ endpoints.

This demonstrates how
"""
# We're doing dynamic import cause this lives within examples/
# navigate to the examples directory to read more about this!
chat_application = importlib.import_module(
    "burr.examples.multi-modal-chatbot.application"
)  # noqa: F401

# the app is commented out as we dynamically register it
# app = FastAPI()

router = APIRouter()


class ChatItem(pydantic.BaseModel):
    """Pydantic model for a chat item. This is used to render the chat history."""

    content: str
    type: Literal["image", "text", "code", "error"]
    role: Literal["user", "assistant"]


@functools.lru_cache(maxsize=128)
def _get_application(project_id: str, app_id: str) -> Application:
    """Quick tool to get the application -- caches it"""
    chat_app = chat_application.application(app_id=app_id, project_id=project_id)
    return chat_app


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
    chat_application.application(app_id=app_id, project_id=project_id)
    return app_id  # just return it for now


# def register(app: FastAPI, api_prefix: str):
#     app.post(
#         f"{api_prefix}/{{project_id}}/{{app_id}}/response",
#         response_model=List[ChatItem])(chat_response)
#     app.get(f"{api_prefix}/{{project_id}}/{{app_id}}/history", response_model=List[ChatItem])(
#         chat_history
#     )
#     app.post(f"{api_prefix}/{{project_id}}/{{app_id}}/create", response_model=str)(
#         create_new_application
#     )
