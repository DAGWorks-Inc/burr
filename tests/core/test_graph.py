from typing import Callable

import pytest

from burr.core import Action, Condition, Result, State, default
from burr.core.graph import GraphBuilder, _validate_actions, _validate_transitions


# TODO -- share versions among tests, this is duplicated in test_application.py
class PassedInAction(Action):
    def __init__(
        self,
        reads: list[str],
        writes: list[str],
        fn: Callable[..., dict],
        update_fn: Callable[[dict, State], State],
        inputs: list[str],
        tags: list[str] = None,
    ):
        super(PassedInAction, self).__init__()
        self._reads = reads
        self._writes = writes
        self._fn = fn
        self._update_fn = update_fn
        self._inputs = inputs
        self._tags = tags

    def run(self, state: State, **run_kwargs) -> dict:
        return self._fn(state, **run_kwargs)

    @property
    def inputs(self) -> list[str]:
        return self._inputs

    def update(self, result: dict, state: State) -> State:
        return self._update_fn(result, state)

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def tags(self) -> list[str]:
        return self._tags or []


def test__validate_transitions_correct():
    _validate_transitions(
        [("counter", "counter", Condition.expr("count < 10")), ("counter", "result", default)],
        {"counter", "result"},
    )


def test__validate_transitions_missing_action():
    with pytest.raises(ValueError, match="not found"):
        _validate_transitions(
            [
                ("counter", "counter", Condition.expr("count < 10")),
                ("counter", "result", default),
            ],
            {"counter"},
        )


def test__validate_transitions_redundant_transition():
    with pytest.raises(ValueError, match="redundant"):
        _validate_transitions(
            [
                ("counter", "counter", Condition.expr("count < 10")),
                ("counter", "result", default),
                ("counter", "counter", default),  # this is unreachable as we already have a default
            ],
            {"counter", "result"},
        )


def test__validate_actions_valid():
    _validate_actions([Result("test")])


def test__validate_actions_empty():
    with pytest.raises(ValueError, match="at least one"):
        _validate_actions([])


base_counter_action = PassedInAction(
    reads=["count"],
    writes=["count"],
    fn=lambda state: {"count": state.get("count", 0) + 1},
    update_fn=lambda result, state: state.update(**result),
    inputs=[],
    tags=["tag1", "tag2"],
)


def test_graph_builder_builds():
    graph = (
        GraphBuilder()
        .with_actions(counter=base_counter_action, result=Result("count"))
        .with_transitions(
            ("counter", "counter", Condition.expr("count < 10")), ("counter", "result")
        )
        .build()
    )
    assert len(graph.actions) == 2
    assert len(graph.transitions) == 2


def test_graph_builder_get_next_node():
    graph = (
        GraphBuilder()
        .with_actions(counter=base_counter_action, result=Result("count"))
        .with_transitions(
            ("counter", "counter", Condition.expr("count < 10")), ("counter", "result")
        )
        .build()
    )
    assert len(graph.actions) == 2
    assert len(graph.transitions) == 2
    assert graph.get_next_node(None, State({"count": 0}), entrypoint="counter").name == "counter"


def test_get_actions_by_tag():
    action_with_tags = PassedInAction(
        reads=["count"],
        writes=["count"],
        fn=lambda state: {"count": state.get("count", 0) + 1},
        update_fn=lambda result, state: state.update(**result),
        inputs=[],
        tags=["tag1", "tag2"],
    )

    action_with_tags_2 = PassedInAction(
        reads=["count"],
        writes=["count"],
        fn=lambda state: {"count": state.get("count", 0) + 1},
        update_fn=lambda result, state: state.update(**result),
        inputs=[],
        tags=["tag1", "tag3"],
    )
    graph = (
        GraphBuilder()
        .with_actions(counter1=action_with_tags, counter2=action_with_tags_2)
        .with_transitions(("counter1", "counter2"))
        .with_transitions(("counter2", "counter1"))
        .build()
    )
    # tag1 is in both actions, tag2 is in one, tag3 is in one
    assert len(graph.get_actions_by_tag("tag1")) == 2
    assert len(graph.get_actions_by_tag("tag2")) == 1
    assert len(graph.get_actions_by_tag("tag3")) == 1
    with pytest.raises(ValueError, match="not found"):
        graph.get_actions_by_tag("tag4")
