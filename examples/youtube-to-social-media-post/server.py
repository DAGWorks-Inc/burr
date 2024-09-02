import contextlib
import logging

import fastapi
import uvicorn
from application import (
    ApplicationState,
    ApplicationStateStream,
    build_application,
    build_application_iterator_streaming,
)
from fastapi.responses import StreamingResponse

from burr.core import Application

logger = logging.getLogger(__name__)

# define a global `burr_app` variable
burr_app: Application[ApplicationState] = None
# Second variant -- this uses a stream + a self-loop
# Note this will save a *lot* to the tracker, each stream!
burr_app_streaming_iterator: Application[ApplicationStateStream] = None


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Instantiate the Burr application on FastAPI startup."""
    # set value for the global `burr_app` variable
    global burr_app, burr_app_streaming_iterator
    burr_app = build_application()
    burr_app_streaming_iterator = build_application_iterator_streaming()
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.get("/social_media_post", response_model=ApplicationState)
def social_media_post(youtube_url: str) -> ApplicationState:
    """Creates a completion for the chat message"""
    _, _, state = burr_app.run(halt_after=["generate_post"], inputs={"youtube_url": youtube_url})

    return state.data


@app.get("/social_media_post_streaming_1", response_model=StreamingResponse)
def social_media_post_streaming(youtube_url: str) -> StreamingResponse:
    """Creates a completion for the chat message"""

    def gen():
        for action, _, state in burr_app_streaming_iterator.iterate(
            halt_after=["final"], inputs={"youtube_url": youtube_url}
        ):
            yield state.data.model_dump_json()

    return StreamingResponse(gen())


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=7443, reload=True)
