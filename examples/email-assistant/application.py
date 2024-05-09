import functools
import os
from typing import Tuple

import openai

from burr.core import Application, ApplicationBuilder, State, action, expr
from burr.tracking import LocalTrackingClient


@functools.lru_cache
def _get_openai_client():
    openai_client = openai.Client()
    return openai_client


@action(reads=[], writes=["incoming_email", "response_instructions"])
def process_input(
    state: State, email_to_respond: str, response_instructions: str
) -> Tuple[dict, State]:
    """Processes input from user and updates state with the input."""
    result = {"incoming_email": email_to_respond, "response_instructions": response_instructions}
    return result, state.update(**result)


@action(reads=[], writes=["has_openai_key"])
def check_openai_key(state: State) -> Tuple[dict, State]:
    result = {"has_openai_key": "OPENAI_API_KEY" in os.environ}
    return result, state.update(**result)


@action(reads=["response_instructions", "incoming_email"], writes=["clarification_questions"])
def determine_clarifications(state: State) -> Tuple[dict, State]:
    """Determines if the response instructions require clarification."""
    # TODO -- query an LLM to determine if the response instructions are clear, or if it needs more information
    incoming_email = state["incoming_email"]
    response_instructions = state["response_instructions"]
    client = _get_openai_client()
    # TODO -- use instructor to get a pydantic model
    result = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a chatbot that has the task of generating responses to an email on behalf of a user. ",
            },
            {
                "role": "user",
                "content": (
                    f"The email you are to respond to is: {incoming_email}."
                    f"Your instructions are: {response_instructions}."
                    "Your first task is to ask any clarifying questions for the user"
                    " who is asking you to respond to this email. These clarifying questions are for the user, "
                    "*not* for the original sender of the email. Please "
                    "generate a list of at most 3 questions (and you really can do less -- 2, 1, or even none are OK! joined by newlines, included only if you feel that you could leverage "
                    "clarification (my time is valuable)."
                    "The questions, joined by newlines, must be the only text you return. If you do not need clarification, return an empty string."
                ),
            },
        ],
    )
    content = result.choices[0].message.content
    all_questions = content.split("\n") if content else []
    return {"clarification_questions": all_questions}, state.update(
        clarification_questions=all_questions
    )


@action(reads=["clarification_questions"], writes=["clarification_answers"])
def clarify_instructions(state: State, clarification_inputs: list[str]) -> Tuple[dict, State]:
    """Clarifies the response instructions if needed."""
    clarification_answers = list(clarification_inputs)
    return {"clarification_answers": clarification_answers}, state.update(
        clarification_answers=clarification_answers
    )


@action(
    reads=[
        "incoming_email",
        "response_instructions",
        "clarification_answers",
        "clarification_questions",
        "draft_history",
        "feedback",
    ],
    writes=["current_draft", "draft_history"],
)
def formulate_draft(state: State) -> Tuple[dict, State]:
    """Formulates the draft response based on the incoming email, response instructions, and any clarifications."""
    # TODO -- query an LLM to generate the draft response
    incoming_email = state["incoming_email"]
    response_instructions = state["response_instructions"]
    client = _get_openai_client()
    # TODO -- use instructor to get a pydantic model
    clarification_answers_formatted_q_a = "\n".join(
        [
            f"Q: {q}\nA: {a}"
            for q, a in zip(
                state["clarification_questions"], state.get("clarification_answers", [])
            )
        ]
    )
    instructions = [
        f"The email you are to respond to is: {incoming_email}.",
        f"Your instructions are: {response_instructions}.",
        "You have already asked the following questions and received the following answers: ",
        clarification_answers_formatted_q_a,
    ]
    if state["draft_history"]:
        instructions.append("Your previous draft was: ")
        instructions.append(state["draft_history"][-1])
        instructions.append(
            "you received the following feedback, please incorporate this into your response: "
        )
        instructions.append(state["feedback"])
    instructions.append("Please generate a draft response using all this information!")
    prompt = " ".join(instructions)

    result = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a chatbot that has the task of generating responses to an email. ",
            },
            {"role": "user", "content": prompt},
        ],
    )
    content = result.choices[0].message.content
    return {"prompt": prompt, "current_draft": content}, state.update(current_draft=content).append(
        draft_history=content
    )


@action(reads=[], writes=["feedback", "feedback_history"])
def process_feedback(state: State, feedback: str) -> Tuple[dict, State]:
    """Processes feedback from user and updates state with the feedback."""
    result = {"feedback": feedback}
    return result, state.update(feedback=feedback).append(feedback_history=feedback)


@action(reads=["current_draft", "feedback"], writes=["final_draft"])
def final_result(state: State) -> Tuple[dict, State]:
    """Returns the final result of the process."""
    result = {"final_draft": state["current_draft"]}
    return result, state.update(final_draft=result["final_draft"])


def application(
    app_id: str = None, project: str = "demo_email_assistant", username: str = None
) -> Application:
    tracker = LocalTrackingClient(project=project)
    builder = (
        ApplicationBuilder()
        .with_actions(
            process_input,
            determine_clarifications,
            clarify_instructions,
            formulate_draft,
            process_feedback,
            final_result,
        )
        .with_transitions(
            ("process_input", "determine_clarifications"),
            (
                "determine_clarifications",
                "clarify_instructions",
                expr("len(clarification_questions) > 0"),
            ),
            ("determine_clarifications", "formulate_draft"),
            ("clarify_instructions", "formulate_draft"),
            ("formulate_draft", "process_feedback"),
            ("process_feedback", "formulate_draft", expr("len(feedback) > 0")),
            ("process_feedback", "final_result"),
        )
        .with_tracker("local", project=project)
        .with_identifiers(app_id=app_id, partition_key=username)
        .initialize_from(
            tracker,
            resume_at_next_action=True,
            default_state={"draft_history": []},
            default_entrypoint="process_input",
        )
    )
    return builder.build()


if __name__ == "__main__":
    app = application()
    app.visualize(
        output_file_path="statemachine", include_conditions=True, include_state=True, format="png"
    )
