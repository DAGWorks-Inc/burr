import asyncio
import logging
from typing import Awaitable, Callable

import pytest

from burr.core import State
from burr.core.action import Action, Condition, Result, default
from burr.core.application import (
    Application,
    ApplicationBuilder,
    Transition,
    _arun_function,
    _assert_set,
    _run_function,
    _validate_actions,
    _validate_start,
    _validate_transitions,
)
from burr.lifecycle import (
    PostRunStepHook,
    PostRunStepHookAsync,
    PreRunStepHook,
    PreRunStepHookAsync,
    internal,
)


class PassedInAction(Action):
    def __init__(
        self,
        reads: list[str],
        writes: list[str],
        fn: Callable[[State], dict],
        update_fn: Callable[[dict, State], State],
    ):
        super(PassedInAction, self).__init__()
        self._reads = reads
        self._writes = writes
        self._fn = fn
        self._update_fn = update_fn

    def run(self, state: State) -> dict:
        return self._fn(state)

    def update(self, result: dict, state: State) -> State:
        return self._update_fn(result, state)

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes


class PassedInActionAsync(PassedInAction):
    def __init__(
        self,
        reads: list[str],
        writes: list[str],
        fn: Callable[[State], Awaitable[dict]],
        update_fn: Callable[[dict, State], State],
    ):
        super().__init__(reads=reads, writes=writes, fn=fn, update_fn=update_fn)  # type: ignore

    async def run(self, state: State) -> dict:
        return await self._fn(state)


base_counter_action = PassedInAction(
    reads=["counter"],
    writes=["counter"],
    fn=lambda state: {"counter": state.get("counter", 0) + 1},
    update_fn=lambda result, state: state.update(**result),
)


async def _counter_update_async(state: State) -> dict:
    await asyncio.sleep(0.0001)  # just so we can make this *truly* async
    # does not matter, but more accurately simulates an async function
    return {"counter": state.get("counter", 0) + 1}


base_counter_action_async = PassedInActionAsync(
    reads=["counter"],
    writes=["counter"],
    fn=_counter_update_async,
    update_fn=lambda result, state: state.update(**result),
)


class BrokenStepException(Exception):
    pass


base_broken_action = PassedInAction(
    reads=[],
    writes=[],
    fn=lambda x: exec("raise(BrokenStepException(x))"),
    update_fn=lambda result, state: state,
)

base_broken_action_async = PassedInActionAsync(
    reads=[],
    writes=[],
    fn=lambda x: exec("raise(BrokenStepException(x))"),
    update_fn=lambda result, state: state,
)


def test_run_function():
    """Tests that we can run a function"""
    action = base_counter_action
    state = State({})
    result = _run_function(action, state)
    assert result == {"counter": 1}


def test_run_function_cant_run_async():
    """Tests that we can't run an async function"""
    action = base_counter_action_async
    state = State({})
    with pytest.raises(ValueError, match="async"):
        _run_function(action, state)


async def test_a_run_function():
    """Tests that we can run an async function"""
    action = base_counter_action_async
    state = State({})
    result = await _arun_function(action, state)
    assert result == {"counter": 1}


def test_app_step():
    """Tests that we can run a step in an app"""
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter",
    )
    action, result, state = app.step()
    assert action.name == "counter"
    assert result == {"counter": 1}


def test_app_step_broken(caplog):
    """Tests that we can run a step in an app"""
    broken_action = base_broken_action.with_name("broken_action_unique_name")
    app = Application(
        actions=[broken_action],
        transitions=[Transition(broken_action, broken_action, default)],
        state=State({}),
        initial_step="broken_action_unique_name",
    )
    with caplog.at_level(logging.ERROR):  # it should say the name, that's the only contract for now
        with pytest.raises(BrokenStepException):
            app.step()
    assert "broken_action_unique_name" in caplog.text


def test_app_step_done():
    """Tests that when we cannot run a step, we return None"""
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action], transitions=[], state=State({}), initial_step="counter"
    )
    app.step()
    assert app.step() is None


async def test_app_astep():
    """Tests that we can run an async step in an app"""
    counter_action = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter_async",
    )
    action, result, state = await app.astep()
    assert action.name == "counter_async"
    assert result == {"counter": 1}


async def test_app_astep_broken(caplog):
    """Tests that we can run a step in an app"""
    broken_action = base_broken_action_async.with_name("broken_action_unique_name")
    app = Application(
        actions=[broken_action],
        transitions=[Transition(broken_action, broken_action, default)],
        state=State({}),
        initial_step="broken_action_unique_name",
    )
    with caplog.at_level(logging.ERROR):  # it should say the name, that's the only contract for now
        with pytest.raises(BrokenStepException):
            await app.astep()
    assert "broken_action_unique_name" in caplog.text


async def test_app_astep_done():
    """Tests that when we cannot run a step, we return None"""
    counter_action = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action], transitions=[], state=State({}), initial_step="counter_async"
    )
    await app.astep()
    assert await app.astep() is None


# internal API
def test_app_many_steps():
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter",
    )
    action, result = None, None
    for i in range(100):
        action, result, state = app.step()
    assert action.name == "counter"
    assert result == {"counter": 100}


async def test_app_many_a_steps():
    counter_action = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter_async",
    )
    action, result = None, None
    for i in range(100):
        action, result, state = await app.astep()
    assert action.name == "counter_async"
    assert result == {"counter": 100}


def test_app_iterate():
    result_action = Result(fields=["counter"]).with_name("result")
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    res = []
    gen = app.iterate(until=["result"])
    counter = 0
    try:
        while True:
            action, result, state = next(gen)
            if action.name == "counter":
                assert state["counter"] == counter + 1
                assert result["counter"] == state["counter"]
                counter = result["counter"]
            else:
                res.append(result)
                assert state["counter"] == 10
                assert result["counter"] == 10
    except StopIteration as e:
        stop_iteration_error = e
    generator_result = stop_iteration_error.value
    state, results = generator_result
    assert state["counter"] == 10
    assert len(results) == 1
    (result,) = results
    assert result["counter"] == 10


async def test_app_a_iterate():
    result_action = Result(fields=["counter"]).with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    res = []
    gen = app.aiterate(until=["result"])
    counter = 0
    # Note that we use an async-for loop cause the API is different, this doesn't
    # return anything (async generators are not allowed to).
    async for action, result, state in gen:
        if action.name == "counter":
            assert state["counter"] == counter + 1
            assert result["counter"] == state["counter"]
            counter = result["counter"]
        else:
            res.append(result)
            assert state["counter"] == 10
            assert result["counter"] == 10


def test_app_run():
    result_action = Result(fields=["counter"]).with_name("result")
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    state, results = app.run(until=["result"])
    assert state["counter"] == 10
    assert len(results) == 1
    assert results[0]["counter"] == 10


async def test_app_a_run():
    result_action = Result(fields=["counter"]).with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    state, results = await app.arun(until=["result"])
    assert state["counter"] == 10
    assert len(results) == 1
    (result,) = results
    assert result["counter"] == 10


async def test_app_a_run_async_and_sync():
    result_action = Result(fields=["counter"]).with_name("result")
    counter_action_sync = base_counter_action_async.with_name("counter_sync")
    counter_action_async = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action_sync, counter_action_async, result_action],
        transitions=[
            Transition(counter_action_sync, counter_action_async, Condition.expr("counter < 20")),
            Transition(counter_action_async, counter_action_sync, default),
            Transition(counter_action_sync, result_action, default),
        ],
        state=State({}),
        initial_step="counter_sync",
    )
    state, results = await app.arun(until=["result"])
    assert state["counter"] > 20
    assert len(results) == 1
    (result,) = results
    assert result["counter"] > 20


def test_app_set_state():
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State(),
        initial_step="counter",
    )
    assert "counter" not in app.state  # initial value
    app.step()
    assert app.state["counter"] == 1  # updated value
    state = app.state
    app.update_state(state.update(counter=2))
    assert app.state["counter"] == 2  # updated value


def test_app_get_next_step():
    counter_action_1 = base_counter_action.with_name("counter_1")
    counter_action_2 = base_counter_action.with_name("counter_2")
    counter_action_3 = base_counter_action.with_name("counter_3")
    app = Application(
        actions=[counter_action_1, counter_action_2, counter_action_3],
        transitions=[
            Transition(counter_action_1, counter_action_2, default),
            Transition(counter_action_2, counter_action_3, default),
            Transition(counter_action_3, counter_action_1, default),
        ],
        state=State(),
        initial_step="counter_1",
    )
    # uninitialized -- counter_1
    assert app.get_next_action().name == "counter_1"
    app.step()
    # ran counter_1 -- counter_2
    assert app.get_next_action().name == "counter_2"
    app.step()
    # ran counter_2 -- counter_3
    assert app.get_next_action().name == "counter_3"
    app.step()
    # ran counter_3 -- back to counter_1
    assert app.get_next_action().name == "counter_1"


def test_application_builder_complete():
    app = (
        ApplicationBuilder()
        .with_state(counter=0)
        .with_actions(counter=base_counter_action, result=Result(fields=["counter"]))
        .with_transitions(
            ("counter", "counter", Condition.expr("counter < 10")), ("counter", "result")
        )
        .with_entrypoint("counter")
        .build()
    )
    assert len(app._actions) == 2
    assert len(app._transitions) == 2
    assert app.get_next_action().name == "counter"


def test__validate_transitions_correct():
    _validate_transitions(
        [("counter", "counter", Condition.expr("counter < 10")), ("counter", "result", default)],
        {"counter", "result"},
    )


def test__validate_transitions_missing_action():
    with pytest.raises(ValueError, match="not found"):
        _validate_transitions(
            [
                ("counter", "counter", Condition.expr("counter < 10")),
                ("counter", "result", default),
            ],
            {"counter"},
        )


def test__validate_transitions_redundant_transition():
    with pytest.raises(ValueError, match="redundant"):
        _validate_transitions(
            [
                ("counter", "counter", Condition.expr("counter < 10")),
                ("counter", "result", default),
                ("counter", "counter", default),  # this is unreachable as we already have a default
            ],
            {"counter", "result"},
        )


def test__validate_start_valid():
    _validate_start("counter", {"counter", "result"})


def test__validate_start_not_found():
    with pytest.raises(ValueError, match="not found"):
        _validate_start("counter", {"result"})


def test__validate_actions_valid():
    _validate_actions([Result(["test"])])


def test__validate_actions_empty():
    with pytest.raises(ValueError, match="at least one"):
        _validate_actions([])


def test__asset_set():
    _assert_set("foo", "foo", "bar")


def test__assert_set_unset():
    with pytest.raises(ValueError, match="foo"):
        _assert_set(None, "foo", "bar")


def test_application_builder_unset():
    with pytest.raises(ValueError):
        ApplicationBuilder().build()


def test_application_runs_hooks_sync():
    class ActionTracker(PreRunStepHook, PostRunStepHook):
        def __init__(self):
            self.pre_called = []
            self.post_called = []

        def pre_run_step(self, *, action: Action, **future_kwargs):
            self.pre_called.append(action.name)

        def post_run_step(self, *, action: Action, **future_kwargs):
            self.post_called.append(action.name)

    tracker = ActionTracker()
    counter_action = base_counter_action.with_name("counter")
    result_action = Result(fields=["counter"]).with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("counter >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
    )
    app.run(until=["result"])
    assert set(tracker.pre_called) == {"counter", "result"}
    assert set(tracker.post_called) == {"counter", "result"}
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11


async def test_application_runs_hooks_async():
    class ActionTrackerAsync(PreRunStepHookAsync, PostRunStepHookAsync):
        def __init__(self):
            self.pre_called = []
            self.post_called = []

        async def pre_run_step(self, *, action: Action, **future_kwargs):
            await asyncio.sleep(0.0001)
            self.pre_called.append(action.name)

        async def post_run_step(self, *, action: Action, **future_kwargs):
            await asyncio.sleep(0.0001)
            self.post_called.append(action.name)

    tracker = ActionTrackerAsync()
    counter_action = base_counter_action.with_name("counter")
    result_action = Result(fields=["counter"]).with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("counter >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
    )
    await app.arun(until=["result"])
    assert set(tracker.pre_called) == {"counter", "result"}
    assert set(tracker.post_called) == {"counter", "result"}
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11
