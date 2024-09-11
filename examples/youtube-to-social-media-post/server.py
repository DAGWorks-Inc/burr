import contextlib
import json
import logging

import fastapi
import uvicorn
from application import (
    ApplicationState,
    SocialMediaPost,
    build_application,
    build_streaming_application,
    build_streaming_application_async,
)
from fastapi.responses import StreamingResponse

from burr.core import Application
from burr.core.action import AsyncStreamingResultContainer, StreamingResultContainer

logger = logging.getLogger(__name__)

# define a global `burr_app` variable
burr_app: Application[ApplicationState] = None
# This does streaming, in sync mode
burr_app_streaming: Application[ApplicationState] = None

# And this does streaming, in async mode
burr_app_streaming_async: Application[ApplicationState] = None

DEFAULT_YOUTUBE_URL = "https://www.youtube.com/watch?v=hqutVJyd3TI"


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """Instantiate the Burr application on FastAPI startup."""
    # set value for the global `burr_app` variable
    global burr_app, burr_app_streaming, burr_app_streaming_async
    burr_app = build_application()
    burr_app_streaming = build_streaming_application()
    burr_app_streaming_async = build_streaming_application_async()
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.get("/social_media_post", response_model=SocialMediaPost)
def social_media_post(youtube_url: str = DEFAULT_YOUTUBE_URL) -> SocialMediaPost:
    """Creates a completion for the chat message"""
    _, _, state = burr_app.run(halt_after=["generate_post"], inputs={"youtube_url": youtube_url})

    return state.data.post


@app.get("/social_media_post_streaming_async", response_class=StreamingResponse)
async def social_media_post_streaming_async(
    youtube_url: str = DEFAULT_YOUTUBE_URL,
) -> StreamingResponse:
    """Creates a completion for the chat message"""

    async def gen():
        _, streaming_container = await burr_app_streaming_async.astream_result(
            halt_after=["generate_post"],
            inputs={"youtube_url": youtube_url},
        )  # type: ignore
        streaming_container: AsyncStreamingResultContainer[ApplicationState, SocialMediaPost]
        async for post in streaming_container:
            obj = post.model_dump()
            yield json.dumps(obj)

    return StreamingResponse(gen())


@app.get("/social_media_post_streaming", response_class=StreamingResponse)
def social_media_post_streaming(youtube_url: str = DEFAULT_YOUTUBE_URL) -> StreamingResponse:
    """Creates a completion for the chat message"""

    def gen():
        _, streaming_container = burr_app_streaming.stream_result(
            halt_after=["generate_post"],
            inputs={"youtube_url": youtube_url},
        )  # type: ignore
        streaming_container: StreamingResultContainer[ApplicationState, SocialMediaPost]
        for post in streaming_container:
            obj = post.model_dump()
            yield json.dumps(obj)

    return StreamingResponse(gen())


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=7443, reload=True)
