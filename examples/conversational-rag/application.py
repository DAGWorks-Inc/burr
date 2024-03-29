import pprint
from typing import List, Optional, Tuple

from hamilton import dataflows, driver

import burr.core
from burr.core import Action, Application, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.lifecycle import LifecycleAdapter, PostRunStepHook, PreRunStepHook

# create the pipeline
conversational_rag = dataflows.import_module("conversational_rag")
conversational_rag_driver = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(conversational_rag)
    .build()
)


def bootstrap_vector_db(rag_driver: driver.Driver, input_texts: List[str]) -> object:
    """Bootstrap the vector database with some input texts."""
    return rag_driver.execute(["vector_store"], inputs={"input_texts": input_texts})["vector_store"]


class PrintStepHook(PostRunStepHook, PreRunStepHook):
    """Custom hook to print the action/result after each step."""

    def pre_run_step(self, action: Action, **future_kwargs):
        if action.name == "ai_converse":
            print("🤔 AI is thinking...")
        if action.name == "human_converse":
            print("⏳Processing input from user...")

    def post_run_step(self, *, state: "State", action: Action, result: dict, **future_kwargs):
        if action.name == "human_converse":
            print("🎙💬", result["question"], "\n")
        if action.name == "ai_converse":
            print("🤖💬", result["conversational_rag_response"], "\n")


@action(
    reads=["question", "chat_history"],
    writes=["chat_history"],
)
def ai_converse(state: State, vector_store: object) -> Tuple[dict, State]:
    """AI conversing step. Uses Hamilton to execute the conversational pipeline."""
    result = conversational_rag_driver.execute(
        ["conversational_rag_response"],
        inputs={
            "question": state["question"],
            "chat_history": state["chat_history"],
        },
        # we use overrides here because we want to pass in the vector store
        overrides={
            "vector_store": vector_store,
        },
    )
    new_history = f"AI: {result['conversational_rag_response']}"
    return result, state.append(chat_history=new_history)


@action(
    reads=[],
    writes=["question", "chat_history"],
)
def human_converse(state: State, user_question: str) -> Tuple[dict, State]:
    """Human converse step -- make sure we get input, and store it as state."""
    state = state.update(question=user_question).append(chat_history=f"Human: {user_question}")
    return {"question": user_question}, state


def application(
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    # our initial knowledge base
    input_text = [
        "harrison worked at kensho",
        "stefan worked at Stitch Fix",
        "stefan likes tacos",
        "elijah worked at TwoSigma",
        "elijah likes mango",
        "stefan used to work at IBM",
        "elijah likes to go biking",
        "stefan likes to bake sourdough",
    ]
    vector_store = bootstrap_vector_db(conversational_rag_driver, input_text)
    app = (
        ApplicationBuilder()
        .with_state(
            **{
                "question": "",
                "chat_history": [],
            }
        )
        .with_actions(
            # bind the vector store to the AI conversational step
            ai_converse=ai_converse.bind(vector_store=vector_store),
            human_converse=human_converse,
            terminal=burr.core.Result("chat_history"),
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .with_entrypoint("human_converse")
        .with_tracker(project="demo:conversational-rag", params={"storage_dir": storage_dir})
        .with_identifiers(app_id=app_id, partition_key="sample_user")
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
