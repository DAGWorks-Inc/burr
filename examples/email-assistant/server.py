import functools
import importlib
from typing import Any, Dict, List, Literal, Optional

import pydantic
from fastapi import APIRouter, FastAPI

from burr.core import Application

email_assistant_application = importlib.import_module(
    "burr.examples.email-assistant.application"
)  # noqa: F401

app = FastAPI()
router = APIRouter()


# we want to render this after every response
class EmailAssistantState(pydantic.BaseModel):
    app_id: str
    email_to_respond: Optional[str]
    response_instructions: Optional[str]
    questions: Optional[List[str]]
    answers: Optional[List[str]]
    drafts: List[str]
    feedback_history: List[str]
    final_draft: Optional[str]
    # This stores the next step, which tells the frontend which ones to call
    next_step: Literal["process_input", "clarify_instructions", "process_feedback", None]

    @staticmethod
    def from_app(app: Application):
        state = app.state
        next_action = app.get_next_action()
        # TODO -- consolidate with the above

        if next_action is not None and next_action.name not in (
            "clarify_instructions",
            "process_feedback",
            "process_input",
        ):
            # quick hack -- this just means we're done if its an error
            # TODO -- add recovery
            next_action = None
        return EmailAssistantState(
            app_id=app.uid,
            email_to_respond=state.get("incoming_email"),
            response_instructions=state.get("response_instructions"),
            questions=state.get("clarification_questions"),
            answers=state.get("clarification_answers"),
            drafts=state.get("draft_history", []),
            feedback_history=state.get("feedback_history", []),
            final_draft=state.get("final_draft"),
            next_step=next_action.name if next_action is not None else None,
        )


@functools.lru_cache(maxsize=128)
def _get_application(project_id: str, app_id: str) -> Application:
    """Utility to get the application. Depending on
    your use-case you might want to reload from state every time (or consider cache invalidation)"""
    app = email_assistant_application.application(app_id=app_id, project=project_id)
    return app


def _run_through(project_id: str, app_id: [str], inputs: Dict[str, Any]) -> EmailAssistantState:
    if app_id == "create_new":  # quick hack to allow for null
        app_id = None
    email_assistant_app = _get_application(project_id, app_id)
    email_assistant_app.run(  # Using this as a side-effect, we'll just get the state aft
        halt_before=["clarify_instructions", "process_feedback"],
        halt_after=["final_result"],
        inputs=inputs,
    )
    return EmailAssistantState.from_app(email_assistant_app)


class DraftInit(pydantic.BaseModel):
    email_to_respond: str
    response_instructions: str


@router.post("/create_new/{project_id}/{app_id}")
def create_new_application(project_id: str, app_id: str) -> str:
    app = _get_application(project_id, app_id)
    return app.uid


@router.post("/create/{project_id}/{app_id}")
def initialize_draft(project_id: str, app_id: str, draft_data: DraftInit) -> EmailAssistantState:
    return _run_through(
        project_id,
        app_id,
        dict(
            email_to_respond=draft_data.email_to_respond,
            response_instructions=draft_data.response_instructions,
        ),
    )


class QuestionAnswers(pydantic.BaseModel):
    answers: List[str]


@router.post("/answer_questions/{project_id}/{app_id}")
def answer_questions(
    project_id: str, app_id: str, question_answers: QuestionAnswers
) -> EmailAssistantState:
    return _run_through(project_id, app_id, dict(clarification_inputs=question_answers.answers))


class Feedback(pydantic.BaseModel):
    feedback: str


@router.post("/provide_feedback/{project_id}/{app_id}")
def provide_feedback(project_id: str, app_id: str, feedback: Feedback) -> EmailAssistantState:
    return _run_through(project_id, app_id, dict(feedback=feedback.feedback))


@router.get("/state/{project_id}/{app_id}")
def get_state(project_id: str, app_id: str) -> EmailAssistantState:
    email_assistant_app = _get_application(project_id, app_id)
    return EmailAssistantState.from_app(email_assistant_app)


if __name__ == "__main__":
    import uvicorn

    app.include_router(router, prefix="/")

    uvicorn.run(app, host="localhost", port=7242)
