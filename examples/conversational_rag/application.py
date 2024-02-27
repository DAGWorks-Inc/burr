import pprint
from typing import List, Optional, Tuple

from hamilton import dataflows, driver, lifecycle

import burr.core
from burr.core import Action, Application, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.lifecycle import LifecycleAdapter, PostRunStepHook, PreRunStepHook

conversational_rag = dataflows.import_module("conversational_rag")
conversational_rag_driver = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(conversational_rag)
    .build()
)


class PrintStepHook(PostRunStepHook, PreRunStepHook):
    """Custom hook to print the action/result after each step."""

    def pre_run_step(self, action: Action, **future_kwargs):
        if action.name == "ai_converse":
            print("🤔 AI is thinking...")
        if action.name == "human_converse":
            print("⏳Processing input from user...")

    def post_run_step(self, *, state: "State", action: Action, result: dict, **future_kwargs):
        if action.name == "ai_converse":
            print("💬", result["conversational_rag_response"], "\n")


@action(
    reads=["input_texts", "question", "chat_history"],
    writes=["chat_history"],
)
def ai_converse(state: State) -> Tuple[dict, State]:
    """AI conversing step. This calls out to an API on the Hamilton hub (hub.dagworks.io)
    to do basic RAG"""
    result = conversational_rag_driver.execute(
        ["conversational_rag_response"],
        inputs={
            "input_texts": state["input_texts"],
            "question": state["question"],
            "chat_history": state["chat_history"],
        },
    )
    new_history = f"AI: {result['conversational_rag_response']}"
    return result, state.append(chat_history=new_history)


@action(
    reads=[],
    writes=["question", "chat_history"],
)
def human_converse(state: State, user_question: str) -> Tuple[dict, State]:
    """Human converse step -- this simply massages the state to be the right shape"""
    state = state.update(question=user_question).append(chat_history=f"Human: {user_question}")
    return {"question": user_question}, state


def application(
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    app = (
        ApplicationBuilder()
        .with_state(
            **{
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                    "stefan likes tacos",
                    "elijah worked at TwoSigma",
                    "elijah likes mango",
                    "stefan used to work at IBM",
                    "elijah likes to go biking",
                    "stefan likes to bake sourdough",
                ],
                "question": "",
                "chat_history": [],
            }
        )
        .with_actions(
            ai_converse=ai_converse,
            human_converse=human_converse,
            terminal=burr.core.Result("chat_history"),
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .with_entrypoint("human_converse")
        .with_tracker(
            "demo:conversational-rag", params={"app_id": app_id, "storage_dir": storage_dir}
        )
        .with_hooks(*hooks if hooks else [])
        .build()
    )
    return app


def main():
    """This is one way -- you provide input via the control flow"""
    app = application(hooks=[PrintStepHook()])
    # Comment back in to visualize
    # app.visualize(
    #     output_file_path="conversational_rag", include_conditions=True, view=True, format="png"
    # )
    print(f"Running RAG with initial state:\n {pprint.pformat(app.state.get_all())}")
    while True:
        user_question = input("Ask something (or type exit to quit): ")
        previous_action, result, state = app.run(
            halt_before=["human_converse"],
            halt_after=["terminal"],
            inputs={"user_question": user_question},
        )
        if previous_action.name == "terminal":
            # reached the end
            pprint.pprint(result)
            return


if __name__ == "__main__":
    main()
