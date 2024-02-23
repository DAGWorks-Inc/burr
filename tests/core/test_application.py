import asyncio
import logging
from typing import Awaitable, Callable, Tuple

import pytest

from burr.core import State
from burr.core.action import Action, Condition, Result, SingleStepAction, default
from burr.core.application import (
    PRIOR_STEP,
    Application,
    ApplicationBuilder,
    Transition,
    _arun_function,
    _arun_single_step_action,
    _assert_set,
    _run_function,
    _run_single_step_action,
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
from burr.lifecycle.base import PostApplicationCreateHook


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
    reads=["counter"],
    writes=["counter"],
    fn=lambda state: {"counter": state.get("counter", 0) + 1},
    update_fn=lambda result, state: state.update(**result),
    inputs=[],
)

base_counter_action_with_inputs = PassedInAction(
    reads=["counter"],
    writes=["counter"],
    fn=lambda state, additional_increment: {
        "counter": state.get("counter", 0) + 1 + additional_increment
    },
    update_fn=lambda result, state: state.update(**result),
    inputs=["additional_increment"],
)


async def _counter_update_async(state: State, additional_increment: int = 0) -> dict:
    await asyncio.sleep(0.0001)  # just so we can make this *truly* async
    # does not matter, but more accurately simulates an async function
    return {"counter": state.get("counter", 0) + 1 + additional_increment}


base_counter_action_async = PassedInActionAsync(
    reads=["counter"],
    writes=["counter"],
    fn=_counter_update_async,
    update_fn=lambda result, state: state.update(**result),
    inputs=[],
)

base_counter_action_with_inputs_async = PassedInActionAsync(
    reads=["counter"],
    writes=["counter"],
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


def test__run_function():
    """Tests that we can run a function"""
    action = base_counter_action
    state = State({})
    result = _run_function(action, state, inputs={})
    assert result == {"counter": 1}


def test__run_function_with_inputs():
    """Tests that we can run a function"""
    action = base_counter_action_with_inputs
    state = State({})
    result = _run_function(action, state, inputs={"additional_increment": 1})
    assert result == {"counter": 2}


def test__run_function_cant_run_async():
    """Tests that we can't run an async function"""
    action = base_counter_action_async
    state = State({})
    with pytest.raises(ValueError, match="async"):
        _run_function(action, state, inputs={})


async def test__arun_function():
    """Tests that we can run an async function"""
    action = base_counter_action_async
    state = State({})
    result = await _arun_function(action, state, inputs={})
    assert result == {"counter": 1}


async def test__arun_function_with_inputs():
    """Tests that we can run an async function"""
    action = base_counter_action_with_inputs_async
    state = State({})
    result = await _arun_function(action, state, inputs={"additional_increment": 1})
    assert result == {"counter": 2}


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


base_single_step_counter = SingleStepCounter()
base_single_step_counter_async = SingleStepCounterAsync()
base_single_step_counter_with_inputs = SingleStepCounterWithInputs()
base_single_step_counter_with_inputs_async = SingleStepCounterWithInputsAsync()


def test__run_single_step_action():
    action = base_single_step_counter.with_name("counter")
    state = State({"count": 0, "tracker": []})
    result, state = _run_single_step_action(action, state, inputs={})
    assert result == {"count": 1}
    assert state.subset("count", "tracker").get_all() == {"count": 1, "tracker": [1]}
    result, state = _run_single_step_action(action, state, inputs={})
    assert result == {"count": 2}
    assert state.subset("count", "tracker").get_all() == {"count": 2, "tracker": [1, 2]}


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
    assert state[PRIOR_STEP] == "counter"  # internal contract, not part of the public API


def test_app_step_with_inputs():
    """Tests that we can run a step in an app"""
    counter_action = base_single_step_counter_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter",
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
    )
    with pytest.raises(ValueError, match="Missing the following inputs"):
        app.step(inputs={})


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
    assert state[PRIOR_STEP] == "counter_async"  # internal contract, not part of the public API


async def test_app_astep_with_inputs():
    """Tests that we can run an async step in an app"""
    counter_action = base_single_step_counter_with_inputs_async.with_name("counter_async")
    app = Application(
        actions=[counter_action],
        transitions=[Transition(counter_action, counter_action, default)],
        state=State({"count": 0, "tracker": []}),
        initial_step="counter_async",
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
    )
    with pytest.raises(ValueError, match="Missing the following inputs"):
        await app.astep(inputs={})


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


def test_iterate():
    result_action = Result("counter").with_name("result")
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
    gen = app.iterate(halt_after=["result"])
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
    action, result, state = generator_result
    assert state["counter"] == 10
    assert result["counter"] == 10


def test_iterate_with_inputs():
    result_action = Result("counter").with_name("result")
    counter_action = base_counter_action_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 2")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    gen = app.iterate(
        halt_after=["result"], inputs={"additional_increment": 10}
    )  # make it go quicly to the end
    while True:
        try:
            action, result, state = next(gen)
        except StopIteration as e:
            a, r, s = e.value
            assert r["counter"] == 11  # 1 + 10, for the first one
            break


async def test_aiterate():
    result_action = Result("counter").with_name("result")
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
    gen = app.aiterate(halt_after=["result"])
    counter = 0
    # Note that we use an async-for loop cause the API is different, this doesn't
    # return anything (async generators are not allowed to).
    async for action, result, state in gen:
        if action.name == "counter":
            assert state["counter"] == result["counter"] == counter + 1
            counter = result["counter"]
        else:
            assert state["counter"] == result["counter"] == 10


async def test_aiterate_halt_before():
    result_action = Result("counter").with_name("result")
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
    gen = app.aiterate(halt_before=["result"])
    counter = 0
    # Note that we use an async-for loop cause the API is different, this doesn't
    # return anything (async generators are not allowed to).
    async for action, result, state in gen:
        if action.name == "counter":
            assert state["counter"] == counter + 1
            counter = result["counter"]
        else:
            assert result is None
            assert state["counter"] == 10


async def test_app_aiterate_with_inputs():
    result_action = Result("counter").with_name("result")
    counter_action = base_counter_action_with_inputs_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    gen = app.aiterate(halt_after=["result"], inputs={"additional_increment": 10})
    async for action, result, state in gen:
        if action.name == "counter":
            assert result["counter"] == state["counter"] == 11
        else:
            assert state["counter"] == result["counter"] == 11


def test_run():
    result_action = Result("counter").with_name("result")
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
    action, result, state = app.run(halt_after=["result"])
    assert state["counter"] == 10
    assert result["counter"] == 10


def test_run_halt_before():
    result_action = Result("counter").with_name("result")
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
    action, result, state = app.run(halt_before=["result"])
    assert state["counter"] == 10
    assert result is None
    assert action.name == "result"


def test_run_with_inputs():
    result_action = Result("counter").with_name("result")
    counter_action = base_counter_action_with_inputs.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    action, result, state = app.run(halt_after=["result"], inputs={"additional_increment": 10})
    assert state["counter"] == result["counter"] == 11


async def test_arun():
    result_action = Result("counter").with_name("result")
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
    action, result, state = await app.arun(halt_after=["result"])
    assert state["counter"] == result["counter"] == 10


async def test_arun_halt_before():
    result_action = Result("counter").with_name("result")
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
    action, result, state = await app.arun(halt_before=["result"])
    assert state["counter"] == 10
    assert result is None
    assert action.name == "result"


async def test_arun_with_inputs():
    result_action = Result("counter").with_name("result")
    counter_action = base_counter_action_with_inputs_async.with_name("counter")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, counter_action, Condition.expr("counter < 10")),
            Transition(counter_action, result_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    action, result, state = await app.arun(
        halt_after=["result"], inputs={"additional_increment": 10}
    )
    assert state["counter"] == result["counter"] == 11


async def test_app_a_run_async_and_sync():
    result_action = Result("counter").with_name("result")
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
    action, result, state = await app.arun(halt_after=["result"])
    assert state["counter"] > 20
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
        .with_actions(counter=base_counter_action, result=Result("counter"))
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
    result_action = Result("counter").with_name("result")
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
    app.run(halt_after=["result"])
    assert set(tracker.pre_called) == {"counter", "result"}
    assert set(tracker.post_called) == {"counter", "result"}
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11


async def test_application_run_step_hooks_async():
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
    result_action = Result("counter").with_name("result")
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
    await app.arun(halt_after=["result"])
    assert set(tracker.pre_called) == {"counter", "result"}
    assert set(tracker.post_called) == {"counter", "result"}
    assert len(tracker.pre_called) == 11
    assert len(tracker.post_called) == 11


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
    result_action = Result("counter").with_name("result")
    Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("counter >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
        adapter_set=internal.LifecycleAdapterSet(tracker),
    )
    assert "state" in tracker.called_args
    assert "application_graph" in tracker.called_args
    assert tracker.call_count == 1


async def test_application_gives_graph():
    counter_action = base_counter_action.with_name("counter")
    result_action = Result("counter").with_name("result")
    app = Application(
        actions=[counter_action, result_action],
        transitions=[
            Transition(counter_action, result_action, Condition.expr("counter >= 10")),
            Transition(counter_action, counter_action, default),
        ],
        state=State({}),
        initial_step="counter",
    )
    graph = app.graph
    assert len(graph.actions) == 2
    assert len(graph.transitions) == 2
    assert graph.entrypoint.name == "counter"
