from typing import List, Optional, Tuple

import burr.core
from burr.core import Application, Result, State, default, expr
from burr.core.action import action
from burr.lifecycle import LifecycleAdapter


@action(reads=["counter"], writes=["counter"])
def counter(state: State) -> Tuple[dict, State]:
    result = {"counter": state["counter"] + 1}
    print(f"counted to {result['counter']}")
    return result, state.update(**result)


def application(
    count_up_to: int = 10,
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    return (
        burr.core.ApplicationBuilder()
        .with_state(counter=0)
        .with_actions(counter=counter, result=Result("counter"))
        .with_transitions(
            ("counter", "counter", expr(f"counter < {count_up_to}")),
            ("counter", "result", default),
        )
        .with_entrypoint("counter")
        .with_tracker("demo:counter", params={"app_id": app_id, "storage_dir": storage_dir})
        .with_hooks(*hooks if hooks else [])
        .build()
    )


if __name__ == "__main__":
    app = application()
    action, state, result = app.run(halt_after=["result"])
    # app.visualize(output_file_path="digraph", include_conditions=True, view=False, format="png")
    print(state["counter"])
