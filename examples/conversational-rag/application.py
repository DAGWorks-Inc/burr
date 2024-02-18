from typing import Tuple

from burr.core import Action, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.lifecycle import PostRunStepHook
from hamilton import dataflows, driver, lifecycle

conversational_rag = dataflows.import_module("conversational_rag")
converasation_rag_dr = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(conversational_rag)
    .with_adapters(lifecycle.PrintLn(verbosity=2))
    .build()
)


class PrintStepHook(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        print("action=====\n", action)
        print("state======\n", state)


# procedural way to do this
@action(
    reads=["input_texts", "question", "chat_history"],
    writes=["chat_history"],
)
def ai_converse(state: State) -> Tuple[dict, State]:
    result = converasation_rag_dr.execute(
        ["conversational_rag_response"],
        inputs={
            "input_texts": state["input_texts"],
            "question": state["question"],
            "chat_history": state["chat_history"],
        },
    )
    new_history = f"Human: {state['question']}\nAI: {result['conversational_rag_response']}"
    return result, state.append(chat_history=new_history)


# procedural way to do this
@action(
    reads=["chat_history"],
    writes=["question"],
)
def human_converse(state: State) -> Tuple[dict, State]:
    user_question = input("What is your next question: ")
    return {"question": user_question}, state.update(question=user_question)


@action(
    reads=["question"],
    writes=["question"],
)
def human_converse_placeholder(state: State) -> Tuple[dict, State]:
    user_question = state["question"]
    return {"question": user_question}, state


@action(reads=[], writes=[])
def terminal_step(state: State) -> Tuple[dict, State]:
    return {}, state


def use_inputs_within_action():
    """This is one way -- you use inputs within an action."""
    app = (
        ApplicationBuilder()
        .with_state(
            **{
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                    "stefan likes tacos",
                    "elijah worked at TwoSigma",
                ],
                "question": "",
                "chat_history": [],
            }
        )
        .with_actions(
            ai_converse=ai_converse,
            human_converse=human_converse,
            terminal=terminal_step,
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .with_entrypoint("human_converse")
        .with_hooks(PrintStepHook())
        .build()
    )
    app.visualize(
        output_file_path="conversational_rag", include_conditions=True, view=True, format="png"
    )
    app.run(until=["terminal"])
    return


def manipulate_state():
    """This way to run the application manipulates state directly."""
    app = (
        ApplicationBuilder()
        .with_state(
            **{
                "input_texts": [
                    "harrison worked at kensho",
                    "stefan worked at Stitch Fix",
                    "stefan likes tacos",
                    "elijah worked at TwoSigma",
                ],
                "question": "",
                "chat_history": [],
            }
        )
        .with_actions(
            ai_converse=ai_converse,
            human_converse=human_converse_placeholder,
            terminal=terminal_step,
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .with_entrypoint("human_converse")
        .with_hooks(PrintStepHook())
        .build()
    )
    app.visualize(
        output_file_path="conversational_rag", include_conditions=True, view=True, format="png"
    )
    while True:
        action, result, state = app.step()
        if action.name == "human_converse":
            user_question = input("What is your next question: ")
            app.update_state(state.update(question=user_question))
        if action.name == "terminal":
            break


if __name__ == "__main__":
    manipulate_state()
