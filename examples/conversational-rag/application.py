from typing import Tuple

import burr.core
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
    """Custom hook to print the state and action after each step."""

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
    new_history = f"AI: {result['conversational_rag_response']}"
    return result, state.append(chat_history=new_history)


@action(
    reads=[],
    writes=["question", "chat_history"],
)
def human_converse(state: State, user_question: str) -> Tuple[dict, State]:
    state = state.update(question=user_question).append(chat_history=f"Human: {user_question}")
    return {"question": user_question}, state


@action(
    reads=[],
    writes=["question", "chat_history"],
)
def human_converse_input(state: State) -> Tuple[dict, State]:
    user_question = input("What is your question?: ")
    state = state.update(question=user_question).append(chat_history=f"Human: {user_question}")
    return {"question": user_question}, state


def main(input_via_control_flow: bool):
    """This is one way -- you provide input via the control flow"""
    if input_via_control_flow:
        human_action = human_converse
    else:
        human_action = human_converse_input
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
            human_converse=human_action,
            terminal=burr.core.Result("chat_history"),
        )
        .with_transitions(
            ("ai_converse", "human_converse", default),
            ("human_converse", "terminal", expr("'exit' in question")),
            ("human_converse", "ai_converse", default),
        )
        .with_entrypoint("human_converse")
        .with_tracker("demo-conversational-rag")
        .with_hooks(PrintStepHook())
        .build()
    )
    app.visualize(
        output_file_path="conversational_rag", include_conditions=True, view=True, format="png"
    )
    if input_via_control_flow:
        while True:
            user_question = input("What is your question: ")
            action, result, state = app.run(
                halt_before=["human_converse"],
                halt_after=["terminal"],
                inputs={"user_question": user_question},
            )
            if action.name == "terminal":
                # reached the end
                print(result)
                break
    else:
        # async way to run things
        # import asyncio
        # action, result, state = asyncio.run(app.arun(
        #     halt_after=["terminal"],
        # ))
        action, result, state = app.run(
            halt_after=["terminal"],
        )
        print(result)
    return


if __name__ == "__main__":
    import random

    choice = random.choice([True, False])
    main(choice)
