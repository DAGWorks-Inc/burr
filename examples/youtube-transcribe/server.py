import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import application
import fastapi
import uvicorn
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from burr.core import Application

logger = logging.getLogger(__name__)


burr_app: Optional[Application] = None


def get_burr_app() -> Application:
    """Retrieve the global Burr app."""
    if burr_app is None:
        raise RuntimeError("Burr app wasn't instantiated.")
    return burr_app


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Instantiate the Burr application on FastAPI startup."""
    global burr_app
    burr_app = application.build_application()
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: fastapi.Request, burr_app: Application = fastapi.Depends(get_burr_app)
):
    """Creates a completion for the chat message"""
    request_json = await request.json()
    latest_message = request_json["messages"][-1]["content"]

    _, result, _ = burr_app.run(halt_after=["bot_turn"], inputs={"user_input": latest_message})

    return ChatCompletion(
        id=f"{uuid.uuid4()}",
        created=int(time.time()),
        model="burr-app",
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=result["content"],
                ),
                finish_reason="stop",
            )
        ],
    )


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=7442, reload=True)
