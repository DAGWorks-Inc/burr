import logging
from typing import List, Optional, Tuple

import burr.core
from burr.core import Application, Result, State, default, expr
from burr.core.action import action
from burr.core.state import SQLLitePersistence
from burr.lifecycle import LifecycleAdapter

logger = logging.getLogger(__name__)


@action(reads=["counter"], writes=["counter"])
def counter(state: State) -> Tuple[dict, State]:
    result = {"counter": state["counter"] + 1}
    # import random
    # if random.random() < 0.5:
    #     raise ValueError("random error")
    print(f"counted to {result['counter']}")
    return result, state.update(**result)


def application(
    count_up_to: int = 10,
    partition_key: str = "demo-user",
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    persister = SQLLitePersistence("demos.db", "counter")
    persister.initialize()
    logger.info(
        f"{partition_key} has these prior invocations: {persister.list_app_ids(partition_key)}"
    )
    return (
        burr.core.ApplicationBuilder()
        .with_actions(counter=counter, result=Result("counter"))
        .with_transitions(
            ("counter", "counter", expr(f"counter < {count_up_to}")),
            ("counter", "result", default),
        )
        .with_identifiers(partition_key=partition_key, app_id=app_id)
        .initialize_from(
            persister,
            resume_at_next_action=True,
            default_state={"counter": 0},
            default_entry_point="counter",
        )
        .with_state_persister(persister)
        .with_tracker("demo:counter", params={"storage_dir": storage_dir})
        .with_hooks(*hooks if hooks else [])
        .build()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = application(app_id="a7c8e525-58f9-4e84-b4b3-f5b80b5b0d0e")
    action, result, state = app.run(halt_after=["result"])
    # app.visualize(output_file_path="digraph", include_conditions=True, view=False, format="png")
    print(state["counter"])
