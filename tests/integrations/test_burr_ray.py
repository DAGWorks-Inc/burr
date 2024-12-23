import uuid
from typing import Any, Dict, Generator

import pytest
import ray

from burr.core import (
    ApplicationBuilder,
    ApplicationContext,
    GraphBuilder,
    Result,
    State,
    action,
    expr,
)
from burr.core.parallelism import MapStates, RunnableGraph, SubgraphType
from burr.integrations.ray import RayExecutor


@pytest.fixture(scope="module")
def init():
    ray.init()
    yield "initialized"
    ray.shutdown()


def test_ray_executor_simple(init):
    executor = RayExecutor()

    futures = [executor.submit(lambda x: x * x, num) for num in range(0, 10)]
    results = [future.result(timeout=5) for future in futures]  # Adjust timeout as necessary
    expected_results = [num * num for num in range(0, 10)]
    assert results == expected_results, "Each number should be squared correctly"


def test_ray_executor_end_to_end_persistence(init, tmpdir):
    """Largely a duplicate of the test_parallelism test_end_to_end test with a few small changes.
    We don't have persistence as sqlite + ray are not happy together (need to shut down resources
    better, more likely, but really people should use a multi-tennant db. We should consider
    unifying but not worth it now"""

    MIN_NUMBER = 90
    MAX_NUMBER = 100

    # dummy as we want an initial action to decide between odd/even next
    @action(reads=["n"], writes=["n", "original_n"])
    def initial(state: State, __context: ApplicationContext) -> State:
        # This assert ensures we only visit once per app, globally
        # Thus if we're restarting this will break
        return state.update(original_n=state["n"])

    @action(reads=["n"], writes=["n", "n_history"])
    def even(state: State) -> State:
        return state.update(n=state["n"] // 2).append(n_history=state["n"])

    @action(reads=["n"], writes=["n", "n_history"])
    def odd(state: State) -> State:
        return state.update(n=3 * state["n"] + 1).append(n_history=state["n"])

    collatz_graph = (
        GraphBuilder()
        .with_actions(
            initial,
            even,
            odd,
            result=Result("n_history"),
        )
        .with_transitions(
            (["initial", "even"], "result", expr("n == 1")),
            (["initial", "even", "odd"], "even", expr("n % 2 == 0")),
            (["initial", "even", "odd"], "odd", expr("n % 2 != 0")),
        )
        .build()
    )

    @action(reads=[], writes=["ns"])
    def map_step(state: State, min_number: int = MIN_NUMBER, max_number: int = MAX_NUMBER) -> State:
        return state.update(ns=list(range(min_number, max_number)))

    class ParallelCollatz(MapStates):
        def states(
            self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
        ) -> Generator[State, None, None]:
            for item in state["ns"]:
                yield state.update(n=item)

        def action(self, state: State, inputs: Dict[str, Any]) -> SubgraphType:
            return RunnableGraph(
                collatz_graph,
                entrypoint="initial",
                halt_after=["result"],
            )

        def reduce(self, state: State, results: Generator[State, None, None]) -> State:
            new_state = state
            count_mapping = {}
            for result in results:
                count_mapping[result["original_n"]] = len(result["n_history"])
            return new_state.update(counts=count_mapping)

        @property
        def writes(self) -> list[str]:
            return ["counts"]

        @property
        def reads(self) -> list[str]:
            return ["ns"]

    app_id = f"collatz_test_{str(uuid.uuid4())}"
    containing_application = (
        ApplicationBuilder()
        .with_actions(
            map_step,
            parallel_collatz=ParallelCollatz(),
            final=Result("counts"),
        )
        .with_transitions(
            ("map_step", "parallel_collatz"),
            ("parallel_collatz", "final"),
        )
        .with_identifiers(app_id=app_id)
        .with_parallel_executor(RayExecutor)
        .with_entrypoint("map_step")
        .build()
    )
    *_, final_state = containing_application.run(halt_after=["final"])
    assert len(final_state["counts"]) == MAX_NUMBER - MIN_NUMBER
