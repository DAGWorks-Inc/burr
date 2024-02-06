import burr.core
from burr.core import Action, Result, State, default, expr
from burr.lifecycle import StateAndResultsFullLogger


class CounterAction(Action):
    @property
    def reads(self) -> list[str]:
        return ["counter"]

    def run(self, state: State) -> dict:
        return {"counter": state["counter"] + 1}

    @property
    def writes(self) -> list[str]:
        return ["counter"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


def application(count_up_to: int = 10, log_file: str = None):
    return (
        burr.core.ApplicationBuilder()
        .with_state(
            counter=0,
        )
        .with_actions(counter=CounterAction(), result=Result(["counter"]))
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
