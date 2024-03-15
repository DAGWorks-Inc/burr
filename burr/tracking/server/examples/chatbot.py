import functools
from typing import List, Literal

import pydantic
from fastapi import FastAPI
from starlette.requests import Request

from burr.core import Application, State
from burr.tracking import LocalTrackingClient

from examples.gpt import application as chat_application


class ChatItem(pydantic.BaseModel):
    content: str
    type: Literal["image", "text", "code", "error"]
    role: Literal["user", "assistant"]


@functools.lru_cache(maxsize=128)
def _get_application(project_id: str, app_id: str) -> Application:
    app = chat_application.application(use_hamilton=False, app_id=app_id, project_id="demo:chatbot")
    if LocalTrackingClient.app_log_exists(project_id, app_id):
        state, _ = LocalTrackingClient.load_state(project_id, app_id)  # TODO -- handle entrypoint
        app.update_state(
            State(state)
        )  # TODO -- handle the entrypoint -- this will always reset to prompt
    return app


def chat_response(project_id: str, app_id: str, prompt: str) -> List[ChatItem]:
    """Chat response endpoint.

    :param project_id: Project ID to run
    :param app_id: Application ID to run
    :param prompt: Prompt to send to the chatbot
    :return:
    """
    burr_app = _get_application(project_id, app_id)
    _, _, state = burr_app.run(halt_after=["response"], inputs=dict(prompt=prompt))
    return state.get("chat_history", [])


def chat_history(project_id: str, app_id: str) -> List[ChatItem]:
    burr_app = _get_application(project_id, app_id)
    state = burr_app.state
    return state.get("chat_history", [])


async def create_new_application(request: Request, project_id: str, app_id: str) -> str:
    """Quick helper to create a new application. Just returns true, you'll want to fetch afterwards.
    In a better chatbot you'd want to either have the frontend store this and create on demand or return
    the actual application model"""
    # side-effect is to create the application
    chat_application.application(use_hamilton=False, app_id=app_id, project_id=project_id)
    return app_id  # just return it for now


def register(app: FastAPI, api_prefix: str):
    app.post(f"{api_prefix}/{{project_id}}/{{app_id}}/response", response_model=List[ChatItem])(
        chat_response
    )
    app.get(f"{api_prefix}/{{project_id}}/{{app_id}}/history", response_model=List[ChatItem])(
        chat_history
    )
    app.post(f"{api_prefix}/{{project_id}}/{{app_id}}/create", response_model=str)(
        create_new_application
    )
