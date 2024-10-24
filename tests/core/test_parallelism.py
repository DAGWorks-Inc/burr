import asyncio
import dataclasses
import datetime
from random import random
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from burr.common import types as burr_types
from burr.core import (
    Action,
    ApplicationBuilder,
    ApplicationContext,
    ApplicationGraph,
    State,
    action,
    expr,
)
from burr.core.action import Input, Result
from burr.core.graph import GraphBuilder
from burr.core.parallelism import MapActions, MapStates, RunnableGraph
from burr.tracking.base import SyncTrackingClient
from burr.visibility import ActionSpan

old_action = action


@action(reads=["n"], writes=["n_count"])
def start(state: State) -> State:
    print("start", state)
    return state.update(n_count=0)


@action(reads=["n"], writes=["n_count", "n"])
def even(state: State, divisor: int) -> State:
    print("even", state)
    result = {"n": state["n"] // divisor}
    return state.update(**result).increment(n_count=1)


@action(reads=["n"], writes=["n_count", "n"])
def odd(state: State, multiplier: int, adder: int) -> State:
    print("odd", state)
    result = {"n": multiplier * state["n"] + adder}
    return state.update(**result).increment(n_count=1)


@action(reads=["n_count", "n"], writes=[])
def final(state: State) -> Tuple[dict, State]:
    print("final", state)
    return {"n_count": state["n_count"], "n": state["n"]}, state


async def sleep_random():
    await asyncio.sleep(random())


@action(reads=["n"], writes=["n_count"])
async def astart(state: State) -> State:
    await sleep_random()
    print("start", state)
    return state.update(n_count=0)


@action(reads=["n"], writes=["n_count", "n"])
async def aeven(state: State, divisor: int) -> State:
    await sleep_random()
    print("even", state)
    result = {"n": state["n"] // divisor}
    return state.update(**result).increment(n_count=1)


@action(reads=["n"], writes=["n_count", "n"])
async def aodd(state: State, multiplier: int, adder: int) -> State:
    await sleep_random()
    print("odd", state)
    result = {"n": multiplier * state["n"] + adder}
    return state.update(**result).increment(n_count=1)


@action(reads=["n_count", "n"], writes=[])
async def afinal(state: State) -> Tuple[dict, State]:
    await sleep_random()
    print("final", state)
    return {"n_count": state["n_count"], "n": state["n"]}, state


@dataclasses.dataclass
class RecursiveActionTracked:
    state_before: Optional[State]
    state_after: Optional[State]
    action: Action
    app_id: str
    partition_key: str
    sequence_id: int
    children: List["RecursiveActionTracked"] = dataclasses.field(default_factory=list)


class RecursiveActionTracker(SyncTrackingClient):
    """Simple test tracking client for a recursive action"""

    def __init__(self, events: List[RecursiveActionTracked]):
        self.events = events

    def copy(self):
        """Quick way to copy from the current state. This assumes linearity (which is true in this case, as parallelism is delegated)"""
        if self.events:
            current_event = self.events[-1]
            if current_event.state_after is not None:
                raise ValueError("Don't copy if you're not in the middle of an event")
            return RecursiveActionTracker(current_event.children)
        raise ValueError("Don't copy if you're not in the middle of an event")

    def post_application_create(
        self,
        *,
        app_id: str,
        partition_key: Optional[str],
        state: "State",
        application_graph: "ApplicationGraph",
        parent_pointer: Optional[burr_types.ParentPointer],
        spawning_parent_pointer: Optional[burr_types.ParentPointer],
        **future_kwargs: Any,
    ):
        pass

    def pre_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        inputs: Dict[str, Any],
        **future_kwargs: Any,
    ):
        self.events.append(
            RecursiveActionTracked(
                state_before=state,
                state_after=None,
                action=action,
                app_id=app_id,
                partition_key=partition_key,
                sequence_id=sequence_id,
            )
        )

    def post_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        result: Optional[Dict[str, Any]],
        exception: Exception,
        **future_kwargs: Any,
    ):
        self.events[-1].state_after = state

    def pre_start_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass

    def post_end_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass

    def do_log_attributes(
        self,
        *,
        attributes: Dict[str, Any],
        action: str,
        action_sequence_id: int,
        span: Optional["ActionSpan"],
        tags: dict,
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass

    def pre_start_stream(
        self,
        *,
        action: str,
        sequence_id: int,
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass

    def post_stream_item(
        self,
        *,
        item: Any,
        item_index: int,
        stream_initialize_time: datetime.datetime,
        first_stream_item_start_time: datetime.datetime,
        action: str,
        sequence_id: int,
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass

    def post_end_stream(
        self,
        *,
        action: str,
        sequence_id: int,
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        pass


done = expr("(n == 1) or (n_count >= max_iterations)")
is_even = expr("n % 2 == 0")
is_odd = expr("n % 2 != 0")


def build_collatz_graph(
    divisor: int = 2,
    multiplier: int = 3,
    adder: int = 1,
):
    collatz_graph = (
        GraphBuilder()
        .with_actions(
            start=start,
            even=even.bind(divisor=divisor),
            odd=odd.bind(multiplier=multiplier, adder=adder),
            final=final,
        )
        .with_transitions(
            (["start", "even"], "final", done),
            (["start", "even", "odd"], "even", is_even),
            (["start", "even", "odd"], "odd", is_odd),
        )
    ).build()
    return RunnableGraph(collatz_graph, "start", ["final"])


def build_async_collatz_graph(
    divisor: int = 2,
    multiplier: int = 3,
    adder: int = 1,
):
    collatz_graph = (
        GraphBuilder()
        .with_actions(
            start=astart,
            even=aeven.bind(divisor=divisor),
            odd=aodd.bind(multiplier=multiplier, adder=adder),
            final=afinal,
        )
        .with_transitions(
            (["start", "even"], "final", done),
            (["start", "even", "odd"], "even", is_even),
            (["start", "even", "odd"], "odd", is_odd),
        )
    ).build()
    return RunnableGraph(collatz_graph, "start", ["final"])


def test_e2e_map_actions_sync_subgraph():
    standard_collatz_graph = build_collatz_graph()
    modified_collatz_graph = build_collatz_graph(
        divisor=2, multiplier=5, adder=1
    )  # probably doesn't converge...
    second_modified_collatz_graph = build_collatz_graph(
        divisor=2, multiplier=-1, adder=-3
    )  # probably doesn't converge...

    class MapActionsCollatz(MapActions):
        def actions(
            self, state: State, inputs: Dict[str, Any], context: ApplicationContext
        ) -> Generator[Union[Action, Callable, RunnableGraph], None, None]:
            for graph_ in [
                standard_collatz_graph,
                modified_collatz_graph,
                second_modified_collatz_graph,
            ]:
                yield graph_

        def state(self, state: State, inputs: Dict[str, Any]):
            return state.update(max_iterations=100)

        def reduce(self, state: State, states: Generator[State, None, None]) -> State:
            # TODO -- ensure that states is in the correct order...
            # Or decide to key it?
            new_state = state
            for output_state in states:
                new_state = new_state.append(collatz_counts=output_state["n_count"])
            return new_state

        @property
        def writes(self) -> list[str]:
            return ["collatz_counts"]

        @property
        def reads(self) -> list[str]:
            return ["n"]

    app = (
        ApplicationBuilder()
        .with_actions(
            initial_action=Input("n"),
            map_action=MapActionsCollatz(),
            final_action=Result("collatz_counts"),
        )
        .with_transitions(("initial_action", "map_action"), ("map_action", "final_action"))
        .with_entrypoint("initial_action")
        .with_tracker(RecursiveActionTracker(events := []))
        .build()
    )
    action, result, state = app.run(halt_after=["final_action"], inputs={"n": 1000})
    print(events)
    import pdb

    pdb.set_trace()


async def test_e2e_map_actions_async_subgraph():
    standard_collatz_graph = build_async_collatz_graph()
    modified_collatz_graph = build_async_collatz_graph(
        divisor=2, multiplier=5, adder=1
    )  # probably doesn't converge...
    second_modified_collatz_graph = build_async_collatz_graph(
        divisor=2, multiplier=-1, adder=-3
    )  # probably doesn't converge...

    class MapActionsCollatz(MapActions):
        def actions(
            self, state: State, inputs: Dict[str, Any], context: ApplicationContext
        ) -> Generator[Union[Action, Callable, RunnableGraph], None, None]:
            for graph_ in [
                standard_collatz_graph,
                modified_collatz_graph,
                second_modified_collatz_graph,
            ]:
                yield graph_

        def state(self, state: State, inputs: Dict[str, Any]):
            return state.update(max_iterations=state["n"])

        def reduce(self, state: State, states: Generator[State, None, None]) -> State:
            # TODO -- ensure that states is in the correct order...
            # Or deicde to key it?
            new_state = state
            for output_state in states:
                new_state = new_state.append(collatz_counts=output_state["n_count"])
            return new_state

        @property
        def writes(self) -> list[str]:
            return ["collatz_counts"]

        @property
        def reads(self) -> list[str]:
            return ["n"]

    app = (
        ApplicationBuilder()
        .with_actions(
            initial_action=Input("n"),
            map_action=MapActionsCollatz(),
            final_action=Result("collatz_counts"),
        )
        .with_transitions(("initial_action", "map_action"), ("map_action", "final_action"))
        .with_entrypoint("initial_action")
        .with_tracker(RecursiveActionTracker(events := []))
        .build()
    )
    action, result, state = await app.arun(halt_after=["final_action"], inputs={"n": 1000})
    print(events)
    import pdb

    pdb.set_trace()


def test_e2e_map_states_sync_subgraph():
    """Tests the map states action with a subgraph that is run in parallel.
    Collatz conjecture over different starting points"""
    collatz_graph = build_collatz_graph()

    class MapStatesCollatz(MapStates):
        def states(
            self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
        ) -> Generator[State, None, None]:
            for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                yield state.update(n=n**3)  # cubed, why not

        def action(self, state: State, inputs: Dict[str, Any]) -> RunnableGraph:
            return collatz_graph

        def reduce(self, state: State, states: Generator[State, None, None]) -> State:
            # TODO -- ensure that states is in the correct order...
            # Or deicde to key it?
            for state in states:
                state = state.append(collatz_counts=state["n_count"])
            return state

        @property
        def writes(self) -> list[str]:
            return ["collatz_counts"]

        @property
        def reads(self) -> list[str]:
            return ["n"]

    app = (
        ApplicationBuilder()
        .with_actions(
            initial_action=Input("n"),
            map_action=MapStatesCollatz(),
            final_action=Result("collatz_counts"),
        )
        .with_transitions(("initial_action", "map_action"), ("map_action", "final_action"))
        .with_entrypoint("initial_action")
        .with_tracker(RecursiveActionTracker(events := []))
        .build()
    )
    action, result, state = app.run(halt_after=["final_action"])
    print(events)
    import pdb

    pdb.set_trace()


async def test_e2e_map_states_async_subgraph():
    """Tests the map states action with a subgraph that is run in parallel.
    Collatz conjecture over different starting points"""
    collatz_graph = build_async_collatz_graph()

    class MapStatesCollatz(MapStates):
        def states(
            self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
        ) -> Generator[State, None, None]:
            for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                yield state.update(n=n**3)  # cubed, why not

        def action(self, state: State, inputs: Dict[str, Any]) -> RunnableGraph:
            return collatz_graph

        def reduce(self, state: State, states: Generator[State, None, None]) -> State:
            # TODO -- ensure that states is in the correct order...
            # Or deicde to key it?
            for state in states:
                state = state.append(collatz_counts=state["n_count"])
            return state

        @property
        def writes(self) -> list[str]:
            return ["collatz_counts"]

        @property
        def reads(self) -> list[str]:
            return ["n"]

    app = (
        ApplicationBuilder()
        .with_actions(
            initial_action=Input("n"),
            map_action=MapStatesCollatz(),
            final_action=Result("collatz_counts"),
        )
        .with_transitions(("initial_action", "map_action"), ("map_action", "final_action"))
        .with_entrypoint("initial_action")
        .with_tracker(RecursiveActionTracker(events := []))
        .build()
    )
    action, result, state = await app.arun(halt_after=["final_action"])
    print(events)
    import pdb

    pdb.set_trace()
