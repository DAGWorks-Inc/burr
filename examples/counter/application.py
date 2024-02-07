from typing import Tuple

import burr.core
from burr.core import Result, State, default, expr
from burr.core.action import action
from burr.lifecycle import StateAndResultsFullLogger


@action(reads=["counter"], writes=["counter"])
def counter(state: State) -> Tuple[dict, State]:
    result = {"counter": state["counter"] + 1}
    return result, state.update(**result)


def application(count_up_to: int = 10, log_file: str = None):
    return (
        burr.core.ApplicationBuilder()
        .with_state(counter=0)
        .with_actions(counter=counter, result=Result(["counter"]))
        .with_transitions(
            ("counter", "counter", expr(f"counter < {count_up_to}")),
            ("counter", "result", default),
            ("result", "counter", expr("counter == 0")),  # when we've reset, manually
        )
        .with_entrypoint("counter")
        .with_hooks(*[StateAndResultsFullLogger(log_file)] if log_file else [])
        .build()
    )


if __name__ == "__main__":
    app = application(log_file="counter.jsonl")
    state, result = app.run(until=["result"])
    app.visualize(output_file_path="counter.png", include_conditions=True, view=True)
    assert state["counter"] == 10
    print(state["counter"])
