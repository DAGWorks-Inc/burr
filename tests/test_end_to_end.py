"""End-to-end tests -- these are more like integration tests,
but they're specifically meant to be a smoke-screen. If you ever
see failures in these tests, you should make a unit test, demonstrate the failure there,
then fix both in that test and the end-to-end test."""
from io import StringIO
from typing import Any, Tuple
from unittest.mock import patch

from burr.core import Action, ApplicationBuilder, State, action
from burr.core.action import Input, Result, expr
from burr.lifecycle import base


def test_end_to_end_collatz_with_function_api():
    """End-to-end test for collatz conjecture. This is a fun (unproven) finite state machine."""

    class CountHook(base.PostRunStepHook):
        def __init__(self):
            self.count = 0

        def post_run_step(self, action: "Action", **future_kwargs: Any):
            if action.name != "result":
                self.count += 1

    hook = CountHook()

    @action(reads=["n"], writes=["n", "n_history"])
    def even(state: State) -> Tuple[dict, State]:
        result = {"n": state["n"] // 2}
        return result, state.update(**result).append(n_history=result["n"])

    @action(reads=["n"], writes=["n", "n_history"])
    def odd(state: State) -> Tuple[dict, State]:
        result = {"n": 3 * state["n"] + 1}
        return result, state.update(**result).append(n_history=result["n"])

    done = expr("n == 1")
    is_even = expr("n % 2 == 0")
    is_odd = expr("n % 2 != 0")
    application = (
        ApplicationBuilder()
        .with_state(n_history=[])
        .with_actions(
            original=Input("n"),
            even=even,
            odd=odd,
            result=Result("n_history"),
        )
        .with_transitions(
            (["original", "even"], "result", done),
            (["original", "even", "odd"], "even", is_even),
            (["original", "even", "odd"], "odd", is_odd),
        )
        .with_entrypoint("original")
        .with_hooks(hook)
        .build()
    )
    state, [result] = application.run(until=["result"], inputs={"n": 1000})
    assert result["n_history"][-1] == 1
    assert hook.count == 112


def test_echo_bot():
    @action(reads=["prompt"], writes=["response"])
    def echo(state: State) -> Tuple[dict, State]:
        return {"response": state["prompt"]}, state.update(response=state["prompt"])

    application = (
        ApplicationBuilder()
        .with_actions(
            prompt=Input("prompt"),
            response=echo,
        )
        .with_transitions(("prompt", "response"))
        .with_entrypoint("prompt")
        .build()
    )
    prompt = "hello"
    with patch("sys.stdin", new=StringIO(prompt)):
        state, [result] = application.run(until=["response"], inputs={"prompt": input()})

    application.visualize(
        output_file_path="digraph",
        include_conditions=True,
        view=False,
        include_state=True,
        format="png",
    )
    assert result["response"] == prompt
