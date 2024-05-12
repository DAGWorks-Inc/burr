import asyncio
import collections
import logging
from typing import Any, Awaitable, Callable, Dict, Generator, Literal, Optional, Tuple

import pytest

from burr.core import State
from burr.core.action import (
    Action,
    Condition,
    Reducer,
    Result,
    SingleStepAction,
    SingleStepStreamingAction,
    StreamingAction,
    action,
    default,
    expr,
)
from burr.core.application import (
    PRIOR_STEP,
    Application,
    ApplicationBuilder,
    Transition,
    _arun_function,
    _arun_single_step_action,
    _assert_set,
    _run_function,
    _run_multi_step_streaming_action,
    _run_reducer,
    _run_single_step_action,
    _run_single_step_streaming_action,
    _validate_actions,
    _validate_start,
    _validate_transitions,
)
from burr.core.persistence import BaseStatePersister, DevNullPersister, PersistedStateData
from burr.lifecycle import (
    PostRunStepHook,
    PostRunStepHookAsync,
    PreRunStepHook,
    PreRunStepHookAsync,
    internal,
)
from burr.lifecycle.base import PostApplicationCreateHook
from burr.lifecycle.internal import LifecycleAdapterSet


class PassedInAction(Action):
    def __init__(
        self,
        reads: list[str],
        writes: list[str],
        fn: Callable[..., dict],
        update_fn: Callable[[dict, State], State],
        inputs: list[str],
    ):
        super(PassedInAction, self).__init__()
        self._reads = reads
        self._writes = writes
        self._fn = fn
        self._update_fn = update_fn
        self._inputs = inputs

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


class PassedInActionAsync(PassedInAction):
    def __init__(
        self,
        reads: list[str],
        writes: list[str],
        fn: Callable[..., Awaitable[dict]],
        update_fn: Callable[[dict, State], State],
        inputs: list[str],
    ):
        super().__init__(reads=reads, writes=writes, fn=fn, update_fn=update_fn, inputs=inputs)  # type: ignore

    async def run(self, state: State, **run_kwargs) -> dict:
        return await self._fn(state, **run_kwargs)


base_counter_action = PassedInAction(
    reads=["count"],
    writes=["count"],
    fn=lambda state: {"count": state.get("count", 0) + 1},
    update_fn=lambda result, state: state.update(**result),
    inputs=[],
)

base_counter_action_with_inputs = PassedInAction(
    reads=["count"],
    writes=["count"],
    fn=lambda state, additional_increment: {
        "count": state.get("count", 0) + 1 + additional_increment
    },
    update_fn=lambda result, state: state.update(**result),
    inputs=["additional_increment"],
)


class ActionTracker(PreRunStepHook, PostRunStepHook):
    def __init__(self):
        self.pre_called = []
        self.post_called = []

    def pre_run_step(self, action: Action, **future_kwargs):
        self.pre_called.append((action.name, future_kwargs))

    def post_run_step(self, action: Action, **future_kwargs):
        self.post_called.append((action.name, future_kwargs))


class ActionTrackerAsync(PreRunStepHookAsync, PostRunStepHookAsync):
    def __init__(self):
        self.pre_called = []
        self.post_called = []

    async def pre_run_step(self, *, action: Action, **future_kwargs):
        await asyncio.sleep(0.0001)
        self.pre_called.append((action.name, future_kwargs))

    async def post_run_step(self, *, action: Action, **future_kwargs):
        await asyncio.sleep(0.0001)
        self.post_called.append((action.name, future_kwargs))


async def _counter_update_async(state: State, additional_increment: int = 0) -> dict:
    await asyncio.sleep(0.0001)  # just so we can make this *truly* async
    # does not matter, but more accurately simulates an async function
    return {"count": state.get("count", 0) + 1 + additional_increment}


base_counter_action_async = PassedInActionAsync(
    reads=["count"],
    writes=["count"],
    fn=_counter_update_async,
    update_fn=lambda result, state: state.update(**result),
    inputs=[],
)

base_counter_action_with_inputs_async = PassedInActionAsync(
    reads=["count"],
    writes=["count"],
    fn=lambda state, additional_increment: _counter_update_async(
        state, additional_increment=additional_increment
    ),
    update_fn=lambda result, state: state.update(**result),
    inputs=["additional_increment"],
)


class BrokenStepException(Exception):
    pass


base_broken_action = PassedInAction(
    reads=[],
    writes=[],
    fn=lambda x: exec("raise(BrokenStepException(x))"),
    update_fn=lambda result, state: state,
    inputs=[],
)

base_broken_action_async = PassedInActionAsync(
    reads=[],
    writes=[],
    fn=lambda x: exec("raise(BrokenStepException(x))"),
    update_fn=lambda result, state: state,
    inputs=[],
)


async def incorrect(x):
    return "not a dict"


base_action_incorrect_result_type = PassedInAction(
    reads=[],
    writes=[],
    fn=lambda x: "not a dict",
    update_fn=lambda result, state: state,
    inputs=[],
)

base_action_incorrect_result_type_async = PassedInActionAsync(
    reads=[],
    writes=[],
    fn=incorrect,
    update_fn=lambda result, state: state,
    inputs=[],
)


def test__run_function():
    """Tests that we can run a function"""
    action = base_counter_action
    state = State({})
    result = _run_function(action, state, inputs={}, name=action.name)
    assert result == {"count": 1}


def test__run_function_with_inputs():
    """Tests that we can run a function"""
    action = base_counter_action_with_inputs
    state = State({})
    result = _run_function(action, state, inputs={"additional_increment": 1}, name=action.name)
    assert result == {"count": 2}


def test__run_function_cant_run_async():
    """Tests that we can't run an async function"""
    action = base_counter_action_async
    state = State({})
    with pytest.raises(ValueError, match="async"):
        _run_function(action, state, inputs={}, name=action.name)


def test__run_function_incorrect_result_type():
    """Tests that we can run an async function"""
    action = base_action_incorrect_result_type
    state = State({})
    with pytest.raises(ValueError, match="returned a non-dict"):
        _run_function(action, state, inputs={}, name=action.name)


def test__run_reducer_modifies_state():
    """Tests that we can run a reducer and it behaves as expected"""
    reducer = PassedInAction(
        reads=["count"],
        writes=["count"],
        fn=...,
        update_fn=lambda result, state: state.update(**result),
        inputs=[],
    )
    state = State({"count": 0})
    state = _run_reducer(reducer, state, {"count": 1}, "reducer")
    assert state["count"] == 1


def test__run_reducer_deletes_state():
    """Tests that we can run a reducer that deletes an item from state"""
    reducer = PassedInAction(
        reads=["count"],
        writes=[],  # TODO -- figure out how we can better know that it deletes items...ß
        fn=...,
        update_fn=lambda result, state: state.wipe(delete=["count"]),
        inputs=[],
    )
    state = State({"count": 0})
    state = _run_reducer(reducer, state, {}, "deletion_reducer")
    assert "count" not in state


async def test__arun_function():
    """Tests that we can run an async function"""
    action = base_counter_action_async
    state = State({})
    result = await _arun_function(action, state, inputs={}, name=action.name)
    assert result == {"count": 1}


async def test__arun_function_incorrect_result_type():
    """Tests that we can run an async function"""
    action = base_action_incorrect_result_type_async
    state = State({})
    with pytest.raises(ValueError, match="returned a non-dict"):
        await _arun_function(action, state, inputs={}, name=action.name)


async def test__arun_function_with_inputs():
    """Tests that we can run an async function"""
    action = base_counter_action_with_inputs_async
    state = State({})
    result = await _arun_function(
        action, state, inputs={"additional_increment": 1}, name=action.name
    )
    assert result == {"count": 2}


def test_run_reducer_errors_missing_writes():
    class BrokenReducer(Reducer):
        def update(self, result: dict, state: State) -> State:
            return state.update(present_value=1)

        @property
        def writes(self) -> list[str]:
            return ["missing_value", "present_value"]

    reducer = BrokenReducer()
    state = State()
    with pytest.raises(ValueError, match="missing_value"):
        _run_reducer(reducer, state, {}, "broken_reducer")


def test_run_single_step_action_errors_missing_writes():
    class BrokenAction(SingleStepAction):
        @property
        def reads(self) -> list[str]:
            return []

        def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
            return {"present_value": 1}, state.update(present_value=1)

        @property
        def writes(self) -> list[str]:
            return ["missing_value", "present_value"]

    action = BrokenAction()
    state = State()
    with pytest.raises(ValueError, match="missing_value"):
        _run_single_step_action(action, state, inputs={})


async def test_arun_single_step_action_errors_missing_writes():
    class BrokenAction(SingleStepAction):
        @property
        def reads(self) -> list[str]:
            return []

        async def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
            await asyncio.sleep(0.0001)  # just so we can make this *truly* async
            return {"present_value": 1}, state.update(present_value=1)

        @property
        def writes(self) -> list[str]:
            return ["missing_value", "present_value"]

    action = BrokenAction()
    state = State()
    with pytest.raises(ValueError, match="missing_value"):
        await _arun_single_step_action(action, state, inputs={})


def test_run_single_step_streaming_action_errors_missing_write():
    class BrokenAction(SingleStepStreamingAction):
        def stream_run_and_update(
            self, state: State, **run_kwargs
        ) -> Generator[dict, None, Tuple[dict, State]]:
            yield {}
            return {"present_value": 1}, state.update(present_value=1)

        @property
        def reads(self) -> list[str]:
            return []

        @property
        def writes(self) -> list[str]:
            return ["missing_value", "present_value"]

    action = BrokenAction()
    state = State()
    with pytest.raises(ValueError, match="missing_value"):
        gen = _run_single_step_streaming_action(action, state, inputs={})
        collections.deque(gen, maxlen=0)  # exhaust the generator


def test_run_multi_step_streaming_action_errors_missing_write():
    class BrokenAction(StreamingAction):
        def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, dict]:
            yield {}
            return {"present_value": 1}

        def update(self, result: dict, state: State) -> State:
            return state.update(present_value=1)

        @property
        def reads(self) -> list[str]:
            return []

        @property
        def writes(self) -> list[str]:
            return ["missing_value", "present_value"]

    action = BrokenAction()
    state = State()
    with pytest.raises(ValueError, match="missing_value"):
        gen = _run_multi_step_streaming_action(action, state, inputs={})
        collections.deque(gen, maxlen=0)  # exhaust the generator


class SingleStepCounter(SingleStepAction):
    def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        result = {"count": state["count"] + 1 + sum([0] + list(run_kwargs.values()))}
        return result, state.update(**result).append(tracker=result["count"])

    @property
    def reads(self) -> list[str]:
        return ["count"]

    @property
    def writes(self) -> list[str]:
        return ["count", "tracker"]


class SingleStepCounterWithInputs(SingleStepCounter):
    @property
    def inputs(self) -> list[str]:
        return ["additional_increment"]


class SingleStepActionIncorrectResultType(SingleStepAction):
    def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        return "not a dict", state

    @property
    def reads(self) -> list[str]:
        return []

    @property
    def writes(self) -> list[str]:
        return []


class SingleStepActionIncorrectResultTypeAsync(SingleStepActionIncorrectResultType):
    async def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        return "not a dict", state


class SingleStepCounterAsync(SingleStepCounter):
    async def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        await asyncio.sleep(0.0001)  # just so we can make this *truly* async
        return super(SingleStepCounterAsync, self).run_and_update(state, **run_kwargs)

    @property
    def reads(self) -> list[str]:
        return ["count"]

    @property
    def writes(self) -> list[str]:
        return ["count", "tracker"]


class SingleStepCounterWithInputsAsync(SingleStepCounterAsync):
    @property
    def inputs(self) -> list[str]:
        return ["additional_increment"]


class StreamingCounter(StreamingAction):
    def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, dict]:
        if "steps_per_couunt" in run_kwargs:
            steps_per_count = run_kwargs["granularity"]
        else:
            steps_per_count = 10
        count = state["count"]
        for i in range(steps_per_count):
            yield {"count": count + ((i + 1) / 10)}
        return {"count": count + 1}

    @property
    def reads(self) -> list[str]:
        return ["count"]

    @property
    def writes(self) -> list[str]:
        return ["count", "tracker"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result).append(tracker=result["count"])


class SingleStepStreamingCounter(SingleStepStreamingAction):
    def stream_run_and_update(
        self, state: State, **run_kwargs
    ) -> Generator[dict, None, Tuple[dict, State]]:
        steps_per_count = run_kwargs.get("granularity", 10)
        count = state["count"]
        for i in range(steps_per_count):
            yield {"count": count + ((i + 1) / 10)}
        return {"count": count + 1}, state.update(count=count + 1).append(tracker=count + 1)

    @property
    def reads(self) -> list[str]:
        return ["count"]

    @property
    def writes(self) -> list[str]:
        return ["count", "tracker"]


class StreamingActionIncorrectResultType(StreamingAction):
    def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, dict]:
        yield {}
        return "not a dict"

    @property
    def reads(self) -> list[str]:
        return []

    @property
    def writes(self) -> list[str]:
        return []

    def update(self, result: dict, state: State) -> State:
        return state


class StreamingSingleStepActionIncorrectResultType(SingleStepStreamingAction):
    def stream_run_and_update(
        self, state: State, **run_kwargs
    ) -> Generator[dict, None, Tuple[dict, State]]:
        yield {}
        return "not a dict", state

    @property
    def reads(self) -> list[str]:
        return []

    @property
    def writes(self) -> list[str]:
        return []


base_single_step_counter = SingleStepCounter()
base_single_step_counter_async = SingleStepCounterAsync()
base_single_step_counter_with_inputs = SingleStepCounterWithInputs()
base_single_step_counter_with_inputs_async = SingleStepCounterWithInputsAsync()

base_streaming_counter = StreamingCounter()
base_streaming_single_step_counter = SingleStepStreamingCounter()

base_single_step_action_incorrect_result_type = SingleStepActionIncorrectResultType()
base_single_step_action_incorrect_result_type_async = SingleStepActionIncorrectResultTypeAsync()


def test__run_single_step_action():
    action = base_single_step_counter.with_name("counter")
    state = State({"count": 0, "tracker": []})
    result, state = _run_single_step_action(action, state, inputs={})
    assert result == {"count": 1}
    assert state.subset("count", "tracker").get_all() == {"count": 1, "tracker": [1]}
    result, state = _run_single_step_action(action, state, inputs={})
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [1, 2]}


def test__run_single_step_action_incorrect_result_type():
    action = base_single_step_action_incorrect_result_type.with_name("counter")
    state = State({"count": 0, "tracker": []})
    with pytest.raises(ValueError, match="returned a non-dict"):
        _run_single_step_action(action, state, inputs={})


async def test__arun_single_step_action_incorrect_result_type():
    action = base_single_step_action_incorrect_result_type_async.with_name("counter")
    state = State({"count": 0, "tracker": []})
    with pytest.raises(ValueError, match="returned a non-dict"):
        await _arun_single_step_action(action, state, inputs={})


def test__run_single_step_action_with_inputs():
    action = base_single_step_counter_with_inputs.with_name("counter")
    state = State({"count": 0, "tracker": []})
    result, state = _run_single_step_action(action, state, inputs={"additional_increment": 1})
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [2]}
    result, state = _run_single_step_action(action, state, inputs={"additional_increment": 1})
    assert result == {"count": 4}
    assert state.subset("count", "tracker").get_all() == {"count": 4, "tracker": [2, 4]}


async def test__arun_single_step_action():
    action = base_single_step_counter_async.with_name("counter")
    state = State({"count": 0, "tracker": []})
    result, state = await _arun_single_step_action(action, state, inputs={})
    assert result == {"count": 1}
    assert state.subset("count", "tracker").get_all() == {"count": 1, "tracker": [1]}
    result, state = await _arun_single_step_action(action, state, inputs={})
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [1, 2]}


async def test__arun_single_step_action_with_inputs():
    action = base_single_step_counter_with_inputs_async.with_name("counter")
    state = State({"count": 0, "tracker": []})
    result, state = await _arun_single_step_action(
        action, state, inputs={"additional_increment": 1}
    )
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [2]}
    result, state = await _arun_single_step_action(
        action, state, inputs={"additional_increment": 1}
    )
    assert result == {"count": 4}
    assert state.subset("count", "tracker").get_all() == {"count": 4, "tracker": [2, 4]}


class SingleStepActionWithDeletion(SingleStepAction):
    def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        return {}, state.wipe(delete=["to_delete"])

    @property
    def reads(self) -> list[str]:
        return []

    @property
    def writes(self) -> list[str]:
        return []


def test__run_single_step_action_deletes_state():
    action = SingleStepActionWithDeletion()
    state = State({"to_delete": 0})
    result, state = _run_single_step_action(action, state, inputs={})
    assert "to_delete" not in state


def test__run_multistep_streaming_action():
    action = base_streaming_counter.with_name("counter")
    state = State({"count": 0, "tracker": []})
    generator = _run_multi_step_streaming_action(action, state, inputs={})
    last_result = -1
    try:
        while True:
            result = next(generator)
            assert result["count"] > last_result
            last_result = result["count"]
    except StopIteration as e:
        result, state = e.value
        assert result == {"count": 1}
        assert state.subset("count", "tracker").get_all() == {"count": 1, "tracker": [1]}


def test__run_streaming_action_incorrect_result_type():
    action = StreamingActionIncorrectResultType()
    state = State()
    with pytest.raises(ValueError, match="returned a non-dict"):
        gen = _run_multi_step_streaming_action(action, state, inputs={})
        collections.deque(gen, maxlen=0)  # exhaust the generator


def test__run_single_step_streaming_action_incorrect_result_type():
    action = StreamingSingleStepActionIncorrectResultType()
    state = State()
    with pytest.raises(ValueError, match="returned a non-dict"):
        gen = _run_single_step_streaming_action(action, state, inputs={})
        collections.deque(gen, maxlen=0)  # exhaust the generator


def test__run_single_step_streaming_action():
    action = base_streaming_single_step_counter.with_name("counter")
    state = State({"count": 0, "tracker": []})
    generator = _run_single_step_streaming_action(action, state, inputs={})
    last_result = -1
    try:
        while True:
            result = next(generator)
            assert result["count"] > last_result
            last_result = result["count"]
    except StopIteration as e:
        result, state = e.value
        assert result == {"count": 1}
        assert state.subset("count", "tracker").get_all() == {"count": 1, "tracker": [1]}


class SingleStepActionWithDeletionAsync(SingleStepActionWithDeletion):
    async def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        return {}, state.wipe(delete=["to_delete"])


async def test__arun_single_step_action_deletes_state():
    action = SingleStepActionWithDeletionAsync()
    state = State({"to_delete": 0})
    result, state = await _arun_single_step_action(action, state, inputs={})
    assert "to_delete" not in state


def test_app_step():
    """Tests that we can run a step in an app"""
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = app.step()
    assert app.sequence_id == 1
    assert action.name == "counter"
    assert result == {"count": 1}
    assert state[PRIOR_STEP] == "counter"  # internal contract, not part of the public API


def test_app_step_with_inputs():
    """Tests that we can run a step in an app"""
    counter_action = base_single_step_counter_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = app.step(inputs={"additional_increment": 1})
    assert action.name == "counter"
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [2]}


def test_app_step_with_inputs_missing():
    """Tests that we can run a step in an app"""
    counter_action = base_single_step_counter_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    with pytest.raises(ValueError, match="missing required inputs"):
        app.step(inputs={})


def test_app_step_broken(caplog):
    """Tests that we can run a step in an app"""
    broken_action = base_broken_action.with_name("broken_action_unique_name")
    app = Application(
        actions=[broken_action],
        transitions=[Transition(broken_action, broken_action, default)],
        state=State({}),
        initial_step="broken_action_unique_name",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    with caplog.at_level(logging.ERROR):  # it should say the name, that's the only contract for now
        with pytest.raises(BrokenStepException):
            app.step()
    assert "broken_action_unique_name" in caplog.text


def test_app_step_done():
    """Tests that when we cannot run a step, we return None"""
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
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
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = await app.astep()
    assert app.sequence_id == 1
    assert action.name == "counter_async"
    assert result == {"count": 1}
    assert state[PRIOR_STEP] == "counter_async"  # internal contract, not part of the public API


async def test_app_astep_with_inputs():
    """Tests that we can run an async step in an app"""
    counter_action = base_single_step_counter_with_inputs_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter_async",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = await app.astep(inputs={"additional_increment": 1})
    assert action.name == "counter_async"
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [2]}


async def test_app_astep_with_inputs_missing():
    """Tests that we can run an async step in an app"""
    counter_action = base_single_step_counter_with_inputs_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter_async",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    with pytest.raises(ValueError, match="missing required inputs"):
        await app.astep(inputs={})


async def test_app_astep_broken(caplog):
    """Tests that we can run a step in an app"""
    broken_action = base_broken_action_async.with_name("broken_action_unique_name")
    app = Application(
        actions=[broken_action],
        transitions=[Transition(broken_action, broken_action, default)],
        state=State({}),
        initial_step="broken_action_unique_name",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    with caplog.at_level(logging.ERROR):  # it should say the name, that's the only contract for now
        with pytest.raises(BrokenStepException):
            await app.astep()
    assert "broken_action_unique_name" in caplog.text


async def test_app_astep_done():
    """Tests that when we cannot run a step, we return None"""
    counter_action = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[],
        state=State({}),
        initial_step="counter_async",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
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
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result = None, None
    for i in range(100):
        action, result, state = app.step()
    assert action.name == "counter"
    assert result == {"count": 100}


async def test_app_many_a_steps():
    counter_action = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({}),
        initial_step="counter_async",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result = None, None
    for i in range(100):
        action, result, state = await app.astep()
    assert action.name == "counter_async"
    assert result == {"count": 100}


def test_iterate():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    res = []
    gen = app.iterate(halt_after=["result"])
    counter = 0
    try:
        while True:
            action, result, state = next(gen)
            if action.name == "counter":
                assert state["count"] == counter + 1
                assert result["count"] == state["count"]
                counter = result["count"]
            else:
                res.append(result)
                assert state["count"] == 10
                assert result["count"] == 10
    except StopIteration as e:
        stop_iteration_error = e
    generator_result = stop_iteration_error.value
    action, result, state = generator_result
    assert state["count"] == 10
    assert result["count"] == 10
    assert app.sequence_id == 11


def test_iterate_with_inputs():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 2")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    gen = app.iterate(
        halt_after=["result"], inputs={"additional_increment": 10}
    )  # make it go quicly to the end
    while True:
        try:
            action, result, state = next(gen)
        except StopIteration as e:
            a, r, s = e.value
            assert r["count"] == 11  # 1 + 10, for the first one
            break


async def test_aiterate():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    gen = app.aiterate(halt_after=["result"])
    assert app.sequence_id == 0
    counter = 0
    # Note that we use an async-for loop cause the API is different, this doesn't
    # return anything (async generators are not allowed to).
    async for action_, result, state in gen:
        print("si", app.sequence_id, action_.name, state)
        if action_.name == "counter":
            assert state["count"] == result["count"] == counter + 1
            counter = result["count"]
        else:
            assert state["count"] == result["count"] == 10
    assert app.sequence_id == 11


async def test_aiterate_halt_before():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    gen = app.aiterate(halt_before=["result"])
    counter = 0
    # Note that we use an async-for loop cause the API is different, this doesn't
    # return anything (async generators are not allowed to).
    async for action_, result, state in gen:
        if action_.name == "counter":
            assert state["count"] == counter + 1
            counter = result["count"]
        else:
            assert result is None
            assert state["count"] == 10


async def test_app_aiterate_with_inputs():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_with_inputs_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    gen = app.aiterate(halt_after=["result"], inputs={"additional_increment": 10})
    async for action_, result, state in gen:
        if action_.name == "counter":
            assert result["count"] == state["count"] == 11
        else:
            assert state["count"] == result["count"] == 11


def test_run():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = app.run(halt_after=["result"])
    assert state["count"] == 10
    assert result["count"] == 10


def test_run_halt_before():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action, result, state = app.run(halt_before=["result"])
    assert state["count"] == 10
    assert result is None
    assert action.name == "result"


def test_run_with_inputs():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = app.run(halt_after=["result"], inputs={"additional_increment": 10})
    assert action_.name == "result"
    assert state["count"] == result["count"] == 11


def test_run_with_inputs_multiple_actions():
    """Tests that inputs aren't popped off and are passed through to multiple actions."""
    result_action = Result("count").with_name("result")
    counter_action1 = base_counter_action_with_inputs.with_name("counter1")
    counter_action2 = base_counter_action_with_inputs.with_name("counter2")
    app = Application(
        actions=[counter_action1, counter_action2, result_action],
        transitions=[
            Transition(counter_action1, counter_action1, Condition.expr("count < 10")),
            Transition(counter_action1, counter_action2, Condition.expr("count >= 10")),
            Transition(counter_action2, counter_action2, Condition.expr("count < 20")),
            Transition(counter_action2, result_action, default),
        ],
        state=State({}),
        initial_step="counter1",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = app.run(halt_after=["result"], inputs={"additional_increment": 8})
    assert action_.name == "result"
    assert state["count"] == result["count"] == 27
    assert state["__SEQUENCE_ID"] == 4


async def test_arun():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = await app.arun(halt_after=["result"])
    assert state["count"] == result["count"] == 10
    assert action_.name == "result"


async def test_arun_halt_before():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = await app.arun(halt_before=["result"])
    assert state["count"] == 10
    assert result is None
    assert action_.name == "result"


async def test_arun_with_inputs():
    result_action = Result("count").with_name("result")
    counter_action = base_counter_action_with_inputs_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("count < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = await app.arun(
        halt_after=["result"], inputs={"additional_increment": 10}
    )
    assert state["count"] == result["count"] == 11
    assert action_.name == "result"


async def test_arun_with_inputs_multiple_actions():
    result_action = Result("count").with_name("result")
    counter_action1 = base_counter_action_with_inputs_async.with_name("counter1")
    counter_action2 = base_counter_action_with_inputs_async.with_name("counter2")
    app = Application(
        actions=[counter_action1, counter_action2, result_action],
        transitions=[
            Transition(counter_action1, counter_action1, Condition.expr("count < 10")),
            Transition(counter_action1, counter_action2, Condition.expr("count >= 10")),
            Transition(counter_action2, counter_action2, Condition.expr("count < 20")),
            Transition(counter_action2, result_action, default),
        ],
        state=State({}),
        initial_step="counter1",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = await app.arun(
        halt_after=["result"], inputs={"additional_increment": 8}
    )
    assert state["count"] == result["count"] == 27
    assert action_.name == "result"
    assert state["__SEQUENCE_ID"] == 4


async def test_app_a_run_async_and_sync():
    result_action = Result("count").with_name("result")
    counter_action_sync = base_counter_action_async.with_name("counter_sync")
    counter_action_async = base_counter_action_async.with_name("counter_async")
    app = Application(
        actions=[counter_action_sync, counter_action_async, result_action],
        transitions=[
            Transition(counter_action_sync, counter_action_async, Condition.expr("count < 20")),
            Transition(counter_action_async, counter_action_sync, default),
            Transition(counter_action_sync, result_action, default),
        ],
        state=State({}),
        initial_step="counter_sync",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    action_, result, state = await app.arun(halt_after=["result"])
    assert state["count"] > 20
    assert result["count"] > 20


def test_stream_result_halt_after_unique():
    action_tracker = ActionTracker()
    counter_action = base_streaming_counter.with_name("counter")
    counter_action_2 = base_streaming_counter.with_name("counter_2")
    app = Application(
        actions=[counter_action, counter_action_2],
        transitions=[
            Transition(counter_action, counter_action_2, default),
        ],
        state=State({"count": 0}),
        initial_step="counter",
        adapter_set=LifecycleAdapterSet(action_tracker),
        partition_key="test",
        uid="test-123",
    )
    action_, streaming_container = app.stream_result(halt_after=["counter_2"])
    results = list(streaming_container)
    assert len(results) == 10
    result, state = streaming_container.get()
    assert result["count"] == state["count"] == 2
    assert state["tracker"] == [1, 2]
    assert len(action_tracker.pre_called) == 2
    assert len(action_tracker.post_called) == 2
    assert set(dict(action_tracker.pre_called).keys()) == {"counter", "counter_2"}
    assert set(dict(action_tracker.post_called).keys()) == {"counter", "counter_2"}
    assert [item["sequence_id"] for _, item in action_tracker.pre_called] == [
        0,
        1,
    ]  # ensure sequence ID is respected
    assert [item["sequence_id"] for _, item in action_tracker.post_called] == [
        0,
        1,
    ]  # ensure sequence ID is respected


def test_stream_result_halt_after_single_step():
    action_tracker = ActionTracker()
    counter_action = base_streaming_single_step_counter.with_name("counter")
    counter_action_2 = base_streaming_single_step_counter.with_name("counter_2")
    app = Application(
        actions=[counter_action, counter_action_2],
        transitions=[
            Transition(counter_action, counter_action_2, default),
        ],
        state=State({"count": 0}),
        initial_step="counter",
        adapter_set=LifecycleAdapterSet(action_tracker),
        partition_key="test",
        uid="test-123",
    )
    action_, streaming_container = app.stream_result(halt_after=["counter_2"])
    results = list(streaming_container)
    assert len(results) == 10
    result, state = streaming_container.get()
    assert result["count"] == state["count"] == 2
    assert state["tracker"] == [1, 2]
    assert len(action_tracker.pre_called) == 2
    assert len(action_tracker.post_called) == 2
    assert set(dict(action_tracker.pre_called).keys()) == {"counter", "counter_2"}
    assert set(dict(action_tracker.post_called).keys()) == {"counter", "counter_2"}
    assert [item["sequence_id"] for _, item in action_tracker.pre_called] == [
        0,
        1,
    ]  # ensure sequence ID is respected
    assert [item["sequence_id"] for _, item in action_tracker.post_called] == [
        0,
        1,
    ]  # ensure sequence ID is respected


def test_stream_result_halt_after_run_through_final_streaming():
    """Tests what happens when we have an app that runs through non-streaming
    results before hitting a final streaming result specified by halt_after"""
    action_tracker = ActionTracker()
    counter_non_streaming = base_counter_action.with_name("counter_non_streaming")
    counter_streaming = base_streaming_single_step_counter.with_name("counter_streaming")

    app = Application(
        actions=[counter_non_streaming, counter_streaming],
        transitions=[
            Transition(counter_non_streaming, counter_non_streaming, expr("count < 10")),
            Transition(counter_non_streaming, counter_streaming, default),
        ],
        state=State({"count": 0}),
        initial_step="counter_non_streaming",
        adapter_set=LifecycleAdapterSet(action_tracker),
        partition_key="test",
        uid="test-123",
    )
    action_, streaming_container = app.stream_result(halt_after=["counter_streaming"])
    results = list(streaming_container)
    assert len(results) == 10
    result, state = streaming_container.get()
    assert result["count"] == state["count"] == 11
    assert len(action_tracker.pre_called) == 11
    assert len(action_tracker.post_called) == 11
    assert set(dict(action_tracker.pre_called).keys()) == {
        "counter_streaming",
        "counter_non_streaming",
    }
    assert set(dict(action_tracker.post_called).keys()) == {
        "counter_streaming",
        "counter_non_streaming",
    }
    assert [item["sequence_id"] for _, item in action_tracker.pre_called] == list(
        range(0, 11)
    )  # ensure sequence ID is respected
    assert [item["sequence_id"] for _, item in action_tracker.post_called] == list(
        range(0, 11)
    )  # ensure sequence ID is respected


def test_stream_result_halt_after_run_through_final_non_streaming():
    action_tracker = ActionTracker()
    counter_non_streaming = base_counter_action.with_name("counter_non_streaming")
    counter_final_non_streaming = base_counter_action.with_name("counter_final_non_streaming")

    app = Application(
        actions=[counter_non_streaming, counter_final_non_streaming],
        transitions=[
            Transition(counter_non_streaming, counter_non_streaming, expr("count < 10")),
            Transition(counter_non_streaming, counter_final_non_streaming, default),
        ],
        state=State({"count": 0}),
        initial_step="counter_non_streaming",
        adapter_set=LifecycleAdapterSet(action_tracker),
        partition_key="test",
        uid="test-123",
    )
    action, streaming_container = app.stream_result(halt_after=["counter_final_non_streaming"])
    results = list(streaming_container)
    assert len(results) == 0  # nothing to steram
    result, state = streaming_container.get()
    assert result["count"] == state["count"] == 11
    assert len(action_tracker.pre_called) == 11
    assert len(action_tracker.post_called) == 11
    assert set(dict(action_tracker.pre_called).keys()) == {
        "counter_non_streaming",
        "counter_final_non_streaming",
    }
    assert set(dict(action_tracker.post_called).keys()) == {
        "counter_non_streaming",
        "counter_final_non_streaming",
    }
    assert [item["sequence_id"] for _, item in action_tracker.pre_called] == list(
        range(0, 11)
    )  # ensure sequence ID is respected
    assert [item["sequence_id"] for _, item in action_tracker.post_called] == list(
        range(0, 11)
    )  # ensure sequence ID is respected


def test_stream_result_halt_before():
    action_tracker = ActionTracker()
    counter_non_streaming = base_counter_action.with_name("counter_non_streaming")
    counter_streaming = base_streaming_single_step_counter.with_name("counter_final")

    app = Application(
        actions=[counter_non_streaming, counter_streaming],
        transitions=[
            Transition(counter_non_streaming, counter_non_streaming, expr("count < 10")),
            Transition(counter_non_streaming, counter_streaming, default),
        ],
        state=State({"count": 0}),
        initial_step="counter_non_streaming",
        partition_key="test",
        uid="test-123",
        adapter_set=LifecycleAdapterSet(action_tracker),
    )
    action, streaming_container = app.stream_result(halt_after=[], halt_before=["counter_final"])
    results = list(streaming_container)
    assert len(results) == 0  # nothing to steram
    result, state = streaming_container.get()
    assert action.name == "counter_final"  # halt before this one
    assert result is None
    assert state["count"] == 10
    assert [item["sequence_id"] for _, item in action_tracker.pre_called] == list(
        range(0, 10)
    )  # ensure sequence ID is respected
    assert [item["sequence_id"] for _, item in action_tracker.post_called] == list(
        range(0, 10)
    )  # ensure sequence ID is respected


def test_app_set_state():
    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State(),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    assert "counter" not in app.state  # initial value
    app.step()
    assert app.state["count"] == 1  # updated value
    state = app.state
    app.update_state(state.update(count=2))
    assert app.state["count"] == 2  # updated value


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
        partition_key="test",
        uid="test-123",
        sequence_id=0,
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
        .with_state(count=0)
        .with_actions(counter=base_counter_action, result=Result("count"))
        .with_transitions(
            ("counter", "counter", Condition.expr("count < 10")), ("counter", "result")
        )
        .with_entrypoint("counter")
        .build()
    )
    assert len(app._actions) == 2
    assert len(app._transitions) == 2
    assert app.get_next_action().name == "counter"


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


def test__validate_start_valid():
    _validate_start("counter", {"counter", "result"})


def test__validate_start_not_found():
    with pytest.raises(ValueError, match="not found"):
        _validate_start("counter", {"result"})


def test__validate_actions_valid():
    _validate_actions([Result("test")])


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


def test_application_run_step_hooks_sync():
    tracker = ActionTracker()
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count").with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("count >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    app.run(halt_after=["result"])
    assert set(dict(tracker.pre_called).keys()) == {"counter", "result"}
    assert set(dict(tracker.post_called).keys()) == {"counter", "result"}
    # assert sequence id is incremented
    assert tracker.pre_called[0][1]["sequence_id"] == 1
    assert tracker.post_called[0][1]["sequence_id"] == 1
    assert set(tracker.pre_called[0][1].keys()) == {
        "sequence_id",
        "state",
        "inputs",
        "app_id",
        "partition_key",
    }
    assert set(tracker.post_called[0][1].keys()) == {
        "sequence_id",
        "result",
        "state",
        "exception",
        "app_id",
        "partition_key",
    }
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11
    # quick inclusion to ensure that the action is not called when we're done running
    assert app.step() is None  # should be None


async def test_application_run_step_hooks_async():
    tracker = ActionTrackerAsync()
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count").with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("count >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    await app.arun(halt_after=["result"])
    assert set(dict(tracker.pre_called).keys()) == {"counter", "result"}
    assert set(dict(tracker.post_called).keys()) == {"counter", "result"}
    # assert sequence id is incremented
    assert tracker.pre_called[0][1]["sequence_id"] == 1
    assert tracker.post_called[0][1]["sequence_id"] == 1
    assert set(tracker.pre_called[0][1].keys()) == {
        "sequence_id",
        "state",
        "inputs",
        "app_id",
        "partition_key",
    }
    assert set(tracker.post_called[0][1].keys()) == {
        "sequence_id",
        "result",
        "state",
        "exception",
        "app_id",
        "partition_key",
    }
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11


async def test_application_run_step_runs_hooks():
    hooks = [ActionTracker(), ActionTrackerAsync()]

    counter_action = base_counter_action.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(*hooks),
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    await app.astep()
    assert len(hooks[0].pre_called) == 1
    assert len(hooks[0].post_called) == 1
    # assert sequence id is incremented
    assert hooks[0].pre_called[0][1]["sequence_id"] == 1
    assert hooks[0].post_called[0][1]["sequence_id"] == 1
    assert set(hooks[0].pre_called[0][1].keys()) == {
        "sequence_id",
        "state",
        "inputs",
        "app_id",
        "partition_key",
    }
    assert set(hooks[1].pre_called[0][1].keys()) == {
        "sequence_id",
        "state",
        "inputs",
        "app_id",
        "partition_key",
    }
    assert set(hooks[0].post_called[0][1].keys()) == {
        "sequence_id",
        "result",
        "state",
        "exception",
        "app_id",
        "partition_key",
    }
    assert set(hooks[1].post_called[0][1].keys()) == {
        "sequence_id",
        "result",
        "state",
        "exception",
        "app_id",
        "partition_key",
    }
    assert len(hooks[1].pre_called) == 1
    assert len(hooks[1].post_called) == 1


def test_application_post_application_create_hook():
    class PostApplicationCreateTracker(PostApplicationCreateHook):
        def __init__(self):
            self.called_args = None
            self.call_count = 0

        def post_application_create(self, **kwargs):
            self.called_args = kwargs
            self.call_count += 1

    tracker = PostApplicationCreateTracker()
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count").with_name("result")
    Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("count >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    assert "state" in tracker.called_args
    assert "application_graph" in tracker.called_args
    assert tracker.call_count == 1


async def test_application_gives_graph():
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count").with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("count >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        partition_key="test",
        uid="test-123",
        sequence_id=0,
    )
    graph = app.graph
    assert len(graph.actions) == 2
    assert len(graph.transitions) == 2
    assert graph.entrypoint.name == "counter"


def test_application_builder_initialize_does_not_allow_state_setting():
    with pytest.raises(ValueError, match="Cannot call initialize_from"):
        ApplicationBuilder().with_entrypoint("foo").with_state(**{"foo": "bar"}).initialize_from(
            DevNullPersister(),
            resume_at_next_action=True,
            default_state={},
            default_entrypoint="foo",
        )


class BrokenPersister(BaseStatePersister):
    """Broken persistor."""

    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None, **kwargs
    ) -> Optional[PersistedStateData]:
        return dict(
            partition_key="key",
            app_id="id",
            sequence_id=0,
            position="foo",
            state=None,
            created_at="",
            status="completed",
        )

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        return []

    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        return


def test_application_builder_initialize_raises_on_broken_persistor():
    """Persisters should return None when there is no state to be loaded and the default used."""
    with pytest.raises(ValueError, match="but state was None"):
        counter_action = base_counter_action.with_name("counter")
        result_action = Result("count").with_name("result")
        (
            ApplicationBuilder()
            .with_actions(counter_action, result_action)
            .with_transitions(("counter", "result", default))
            .initialize_from(
                BrokenPersister(),
                resume_at_next_action=True,
                default_state={},
                default_entrypoint="foo",
            )
            .build()
        )


def test_application_builder_assigns_correct_actions_with_dual_api():
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count")

    @action(reads=[], writes=[])
    def test_action(state: State) -> Tuple[State, Dict[str, Any]]:
        return state, {}

    app = (
        ApplicationBuilder()
        .with_state(count=0)
        .with_actions(counter_action, test_action, result=result_action)
        .with_transitions()
        .with_entrypoint("counter")
        .build()
    )
    graph = app.graph
    assert {a.name for a in graph.actions} == {"counter", "result", "test_action"}


def test__validate_halt_conditions():
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("count")

    @action(reads=[], writes=[])
    def test_action(state: State) -> Tuple[State, Dict[str, Any]]:
        return state, {}

    app = (
        ApplicationBuilder()
        .with_state(count=0)
        .with_actions(counter_action, test_action, result=result_action)
        .with_transitions()
        .with_entrypoint("counter")
        .build()
    )
    with pytest.raises(ValueError, match="(?=.*no_exist_1)(?=.*no_exist_2)"):
        app._validate_halt_conditions(halt_after=["no_exist_1"], halt_before=["no_exist_2"])
