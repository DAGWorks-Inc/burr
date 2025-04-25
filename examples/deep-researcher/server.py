import functools
import importlib
from fastapi import APIRouter
# from fastapi import FastAPI
import os
from typing import Optional

from burr.core import Application, ApplicationBuilder
from burr.tracking import LocalTrackingClient

# uncomment for local testing
# import application as deep_researcher_application

# We're doing dynamic import cause this lives within examples/ (and that module has dashes)
# navigate to the examples directory to read more about this!
deep_researcher_application = importlib.import_module(
    "burr.examples.deep-researcher.application"
)  # noqa: F401

import pydantic


# uncomment for local testing
# app = FastAPI()
router = APIRouter()

try:
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    OpenAIInstrumentor().instrument()
    opentelemetry_available = True
except ImportError:
    opentelemetry_available = False

# pydantic types


class TopicInput(pydantic.BaseModel):
    research_topic: str


class ResearchSummary(pydantic.BaseModel):
    running_summary: str


@functools.lru_cache(maxsize=128)
def _get_application(project_id: str, app_id: str) -> Application:
    """Utility to get the application. Depending on
    your use-case you might want to reload from state every time (or consider cache invalidation)"""
    graph = deep_researcher_application.graph
    tracker = LocalTrackingClient(project=project_id)
    builder = (
        ApplicationBuilder()
        .with_graph(graph)
        .with_tracker(
            tracker := LocalTrackingClient(project=project_id),
            use_otel_tracing=opentelemetry_available,
        )
        .with_identifiers(app_id=app_id)
        .initialize_from(
            tracker,
            resume_at_next_action=True,
            default_state={"research_loop_count": 0, "running_summary": None},
            default_entrypoint="generate_query",
        )
    )
    return builder.build()


@router.post("/response/{project_id}/{app_id}")
def research_response(project_id: str, app_id: str, topic: TopicInput) -> ResearchSummary:
    burr_app = _get_application(project_id, app_id)
    research_topic = topic.research_topic
    action, state, result = burr_app.run(halt_after=["finalize_summary"], inputs={"research_topic": research_topic})
    summary = burr_app.state.get('running_summary')
    return {'running_summary': summary}


@router.post("/create/{project_id}/{app_id}")
def create_new_application(project_id: str, app_id: str) -> str:
    app = _get_application(project_id, app_id)
    return app.uid


@router.get("/validate")
def validate_environment() -> Optional[str]:
    """Validate the environment"""
    has_openai_api_key = "OPENAI_API_KEY" in os.environ
    has_tavily_api_key = "TAVILY_API_KEY" in os.environ
    if has_openai_api_key and has_tavily_api_key:
        return
    message = ""
    openai_api_message = """
        You have not set an API key for [OpenAI](https://www.openai.com). Do this
        by setting the environment variable `OPENAI_API_KEY` to your key.
        You can get a key at https://platform.openai.com.
    """
    tavily_api_message = """
        You have not set an API key for [Tavily Search](https://tavily.com). Do this
        by setting the environment variable `TAVILY_API_KEY` to your key.
        You can get a key at https://app.tavily.com/home.
    """
    if not has_openai_api_key:
        message = message + openai_api_message
    if not has_tavily_api_key:
        message = message + tavily_api_message
    return (
        message
    )


# uncomment for local testing
# @app.get("/")
# def root():
#    return {"message": "Deep Researcher API"}


# app.include_router(router, prefix="/deep_researcher", tags=["deep-researcher-api"])


if __name__ == "__main__":
    pass
    # uncomment for local testing
    # import uvicorn
    # uvicorn.run(app, host="localhost", port=7242)
