import asyncio
from typing import Generator, Tuple

import pytest

from burr.core import State
from burr.core.action import (
    Action,
    Condition,
    Function,
    Input,
    Result,
    SingleStepAction,
    SingleStepStreamingAction,
    StreamingAction,
    StreamingResultContainer,
    _validate_action_function,
    action,
    create_action,
    default,
    streaming_action,
)


def test_is_async_true():
    class AsyncFunction(Function):
        @property
        def inputs(self) -> list[str]:
            return []

        @property
        def reads(self) -> list[str]:
            return []

        async def run(self, state: State, **run_kwargs) -> dict:
            return {}

    func = AsyncFunction()
    assert func.is_async()


def test_is_async_false():
    class SyncFunction(Function):
        def reads(self) -> list[str]:
            return []

        def run(self, state: State, **run_kwargs) -> dict:
            return {}

    func = SyncFunction()
    assert not func.is_async()


class BasicAction(Action):
    @property
    def reads(self) -> list[str]:
        return ["input_variable"]

    def run(self, state: State) -> dict:
        return {"output_variable": state["input_variable"]}

    @property
    def writes(self) -> list[str]:
        return ["output_variable"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


def test_with_name():
    action = BasicAction()
    assert action.name is None  # Nothing set initially
    with_name = action.with_name("my_action")
    assert with_name.name == "my_action"  # Name set on copy
    assert with_name.reads == action.reads
    assert with_name.writes == action.writes


def test_condition():
    cond = Condition(["foo"], lambda state: state["foo"] == "bar", name="foo")
    assert cond.name == "foo"
    assert cond.reads == ["foo"]
    assert cond.run(State({"foo": "bar"})) == {Condition.KEY: True}
    assert cond.run(State({"foo": "baz"})) == {Condition.KEY: False}


def test_condition_when():
    cond = Condition.when(foo="bar")
    assert cond.name == "foo=bar"
    assert cond.reads == ["foo"]
    assert cond.run(State({"foo": "bar"})) == {Condition.KEY: True}
    assert cond.run(State({"foo": "baz"})) == {Condition.KEY: False}


def test_condition_when_complex():
    cond = Condition.when(foo="bar", baz="qux")
    assert cond.name == "baz=qux, foo=bar"
    assert sorted(cond.reads) == ["baz", "foo"]
    assert cond.run(State({"foo": "bar", "baz": "qux"})) == {Condition.KEY: True}
    assert cond.run(State({"foo": "baz", "baz": "qux"})) == {Condition.KEY: False}
    assert cond.run(State({"foo": "bar", "baz": "corge"})) == {Condition.KEY: False}
    assert cond.run(State({"foo": "baz", "baz": "corge"})) == {Condition.KEY: False}


def test_condition_default():
    cond = default
    assert cond.name == "default"
    assert cond.reads == []
    assert cond.run(State({"foo": "bar"})) == {Condition.KEY: True}


def test_condition_expr():
    cond = Condition.expr("foo == 'bar'")
    assert cond.name == "foo == 'bar'"
    assert cond.reads == ["foo"]
    assert cond.run(State({"foo": "bar"})) == {Condition.KEY: True}
    assert cond.run(State({"foo": "baz"})) == {Condition.KEY: False}


def test_condition_expr_complex():
    cond = Condition.expr("foo == 'bar' and baz == 'qux'")
    assert cond.name == "foo == 'bar' and baz == 'qux'"
    assert sorted(cond.reads) == ["baz", "foo"]
    assert cond.run(State({"foo": "bar", "baz": "qux"})) == {Condition.KEY: True}
    assert cond.run(State({"foo": "baz", "baz": "qux"})) == {Condition.KEY: False}
    assert cond.run(State({"foo": "bar", "baz": "corge"})) == {Condition.KEY: False}
    assert cond.run(State({"foo": "baz", "baz": "corge"})) == {Condition.KEY: False}


def test_condition__validate_success():
    cond = Condition.when(foo="bar")
    cond._validate(State({"foo": "bar"}))


def test_condition__validate_failure():
    cond = Condition.when(foo="bar")
    with pytest.raises(ValueError, match="foo"):
        cond._validate(State({"baz": "baz"}))


def test_condition_invert():
    cond = Condition(
        ["foo"],
        lambda state: state["foo"] == "bar",
        name="foo == 'bar'",
    )
    cond_inverted = ~cond
    assert cond_inverted.name == "~foo == 'bar'"
    assert cond_inverted.reads == ["foo"]
    assert cond_inverted.run(State({"foo": "bar"})) == {Condition.KEY: False}
    assert cond_inverted.run(State({"foo": "baz"})) == {Condition.KEY: True}


def test_result():
    result = Result("foo", "bar")
    assert result.run(State({"foo": "baz", "bar": "qux", "baz": "quux"})) == {
        "foo": "baz",
        "bar": "qux",
    }
    assert result.writes == []  # doesn't write anything
    assert result.reads == ["foo", "bar"]
    # no results
    assert result.update(
        {"foo": "baz", "bar": "qux"}, State({"foo": "baz", "bar": "qux", "baz": "quux"})
    ) == State(
        {"foo": "baz", "bar": "qux", "baz": "quux"}
    )  # no impact


def test_input():
    input_action = Input("foo", "bar")
    assert input_action.reads == []
    assert input_action.writes == ["foo", "bar"]
    assert input_action.inputs == ["foo", "bar"]
    assert (result := input_action.run(State({}), foo="baz", bar="qux")) == {
        "foo": "baz",
        "bar": "qux",
    }
    assert input_action.update(result, State({})).get_all() == {"foo": "baz", "bar": "qux"}


def test_function_based_action():
    @action(reads=["input_variable"], writes=["output_variable"])
    def my_action(state: State) -> Tuple[dict, State]:
        return {"output_variable": state["input_variable"]}, state.update(
            output_variable=state["input_variable"]
        )

    fn_based_action = create_action(my_action, name="my_action")
    assert fn_based_action.single_step
    assert fn_based_action.name == "my_action"
    assert fn_based_action.reads == ["input_variable"]
    assert fn_based_action.writes == ["output_variable"]
    result, state = fn_based_action.run_and_update(State({"input_variable": "foo"}))
    assert result == {"output_variable": "foo"}
    assert state.get_all() == {"input_variable": "foo", "output_variable": "foo"}


def test_function_based_action_with_inputs():
    @action(reads=["input_variable"], writes=["output_variable"])
    def my_action(state: State, bound_input: int, unbound_input: int) -> Tuple[dict, State]:
        res = state["input_variable"] + bound_input + unbound_input
        return {"output_variable": res}, state.update(output_variable=res)

    fn_based_action: SingleStepAction = create_action(
        my_action.bind(bound_input=10), name="my_action"
    )
    assert fn_based_action.inputs == (["unbound_input"], [])
    result, state = fn_based_action.run_and_update(State({"input_variable": 1}), unbound_input=100)
    assert state.get_all() == {"input_variable": 1, "output_variable": 111}
    assert result == {"output_variable": 111}


def test_function_based_action_with_defaults():
    @action(reads=["input_variable"], writes=["output_variable"])
    def my_action(
        state: State, bound_input: int, unbound_input: int, unbound_default_input: int = 1000
    ) -> Tuple[dict, State]:
        res = state["input_variable"] + bound_input + unbound_input + unbound_default_input
        return {"output_variable": res}, state.update(output_variable=res)

    fn_based_action: SingleStepAction = create_action(
        my_action.bind(bound_input=10), name="my_action"
    )
    assert fn_based_action.inputs == (["unbound_input"], ["unbound_default_input"])
    result, state = fn_based_action.run_and_update(State({"input_variable": 1}), unbound_input=100)
    assert state.get_all() == {"input_variable": 1, "output_variable": 1111}
    assert result == {"output_variable": 1111}


def test_function_based_action_with_defaults_unbound():
    # inputs can have defaults -- this tests that we treat them propertly
    @action(reads=["input_variable"], writes=["output_variable"])
    def my_action(
        state: State, unbound_input_1: int, unbound_input_2: int, unbound_default_input: int = 1000
    ) -> Tuple[dict, State]:
        res = state["input_variable"] + unbound_input_1 + unbound_input_2 + unbound_default_input
        return {"output_variable": res}, state.update(output_variable=res)

    fn_based_action: SingleStepAction = create_action(my_action, name="my_action")
    assert fn_based_action.inputs == (
        ["unbound_input_1", "unbound_input_2"],
        ["unbound_default_input"],
    )
    result, state = fn_based_action.run_and_update(
        State({"input_variable": 1}), unbound_input_1=10, unbound_input_2=100
    )
    assert state.get_all() == {"input_variable": 1, "output_variable": 1111}
    assert result == {"output_variable": 1111}


async def test_function_based_action_async():
    @action(reads=["input_variable"], writes=["output_variable"])
    async def my_action(state: State) -> Tuple[dict, State]:
        await asyncio.sleep(0.01)
        return {"output_variable": state["input_variable"]}, state.update(
            output_variable=state["input_variable"]
        )

    fn_based_action = create_action(my_action, name="my_action")
    assert fn_based_action.is_async()
    assert fn_based_action.single_step is True
    assert fn_based_action.name == "my_action"
    assert fn_based_action.reads == ["input_variable"]
    assert fn_based_action.writes == ["output_variable"]
    result, state = await fn_based_action.run_and_update(State({"input_variable": "foo"}))
    assert result == {"output_variable": "foo"}
    assert state.get_all() == {"input_variable": "foo", "output_variable": "foo"}


async def test_function_based_action_with_inputs_async():
    @action(reads=["input_variable"], writes=["output_variable"])
    async def my_action(state: State, bound_input: int, unbound_input: int) -> Tuple[dict, State]:
        await asyncio.sleep(0.01)
        res = state["input_variable"] + bound_input + unbound_input
        return {"output_variable": res}, state.update(output_variable=res)

    fn_based_action: SingleStepAction = create_action(
        my_action.bind(bound_input=10), name="my_action"
    )
    assert fn_based_action.is_async()
    assert fn_based_action.inputs == (["unbound_input"], [])
    result, state = await fn_based_action.run_and_update(
        State({"input_variable": 1}), unbound_input=100
    )
    assert state.get_all() == {"input_variable": 1, "output_variable": 111}
    assert result == {"output_variable": 111}


async def test_function_based_action_with_defaults_async():
    @action(reads=["input_variable"], writes=["output_variable"])
    async def my_action(
        state: State, bound_input: int, unbound_input: int, unbound_default_input: int = 1000
    ) -> Tuple[dict, State]:
        await asyncio.sleep(0.01)
        res = state["input_variable"] + bound_input + unbound_input + unbound_default_input
        return {"output_variable": res}, state.update(output_variable=res)

    fn_based_action: SingleStepAction = create_action(
        my_action.bind(bound_input=10), name="my_action"
    )
    assert fn_based_action.inputs == (["unbound_input"], ["unbound_default_input"])
    result, state = await fn_based_action.run_and_update(
        State({"input_variable": 1}), unbound_input=100
    )
    assert state.get_all() == {"input_variable": 1, "output_variable": 1111}
    assert result == {"output_variable": 1111}


def test_create_action_class_api():
    raw_action = BasicAction()
    created_action = create_action(raw_action, name="my_action")
    assert created_action.name == "my_action"
    assert created_action.reads == raw_action.reads
    assert created_action.writes == raw_action.writes


def test_create_action_fn_api():
    @action(reads=["input_variable"], writes=["output_variable"])
    def test_action(state: State) -> Tuple[dict, State]:
        result = {"output_variable": state["input_variable"]}
        return result, state.update(output_variable=result["output_variable"])

    created_action = create_action(test_action, name="my_action")
    assert created_action.name == "my_action"
    assert created_action.reads == ["input_variable"]
    assert created_action.writes == ["output_variable"]
    assert created_action.single_step
    result, state = created_action.run_and_update(State({"input_variable": "foo"}))
    assert result == {"output_variable": "foo"}
    assert state.get_all() == {"input_variable": "foo", "output_variable": "foo"}


def test_create_action_fn_api_with_bind():
    @action(reads=["input_variable_1"], writes=["output_variable_1", "output_variable_2"])
    def test_action(state: State, input_variable_2: int) -> Tuple[dict, State]:
        result = {
            "output_variable_1": state["input_variable_1"],
            "output_variable_2": input_variable_2,
        }
        return result, state.update(**result)

    bound = test_action.bind(input_variable_2=2)
    created_action = create_action(bound, name="my_action")

    assert created_action.name == "my_action"
    result, state = created_action.run_and_update(State({"input_variable_1": "foo"}))
    assert result == {
        "output_variable_1": "foo",
        "output_variable_2": 2,
    }
    assert state.get_all() == {
        "input_variable_1": "foo",
        "output_variable_1": "foo",
        "output_variable_2": 2,
    }


def test_create_action_streaming_fn_api_with_bind():
    @streaming_action(reads=["input_variable"], writes=["output_variable"])
    def test_action(state: State, prefix: str) -> Generator[dict, None, Tuple[dict, State]]:
        buffer = []
        for c in prefix + state["input_variable"]:
            buffer.append(c)
            yield {"output_variable": c}  # intermediate results
        result = {"output_variable": "".join(buffer)}
        return result, state.update(output_variable=result["output_variable"])

    created_action = create_action(test_action.bind(prefix="prefix_"), name="my_action")
    assert created_action.streaming
    assert isinstance(created_action, SingleStepStreamingAction)
    assert created_action.name == "my_action"
    assert created_action.reads == ["input_variable"]
    assert created_action.writes == ["output_variable"]
    assert created_action.single_step
    gen = created_action.stream_run_and_update(State({"input_variable": "foo"}))
    out = []
    while True:
        try:
            out.append(next(gen)["output_variable"])
        except StopIteration as e:
            result, state = e.value
            assert result == {"output_variable": "prefix_foo"}
            assert state.get_all() == {"input_variable": "foo", "output_variable": "prefix_foo"}
            break
    assert out == list("prefix_foo")


def test_create_action_undecorated_function():
    def test_action(state: State) -> Tuple[dict, State]:
        result = {"output_variable": state["input_variable"]}
        return result, state.update(output_variable=result["output_variable"])

    with pytest.raises(ValueError, match="not a valid action"):
        create_action(test_action, name="my_action")


def test__validate_action_function_invalid_signature_extra_parameters():
    def incorrect_signature(state: State, extra_to_bind: str) -> Tuple[dict, State]:
        pass

    _validate_action_function(incorrect_signature)


def test__validate_action_function_invalid_signature_incorrect_param_type():
    def incorrect_signature(state: int) -> Tuple[dict, State]:
        pass

    with pytest.raises(ValueError, match="single argument"):
        _validate_action_function(incorrect_signature)


def test__validate_action_function_invalid_signature_incorrect_return_type():
    def incorrect_signature(state: State) -> int:
        pass

    with pytest.raises(ValueError, match="must return"):
        _validate_action_function(incorrect_signature)


def test__validate_action_function_invalid_signature_correct():
    def correct_signature(state: State) -> Tuple[dict, State]:
        pass

    _validate_action_function(correct_signature)


def test_streaming_action_stream_run():
    class SimpleStreamingAction(StreamingAction):
        def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, dict]:
            buffer = []
            for char in state["echo"]:
                yield {"response": char}
                buffer.append(char)
            return {"response": "".join(buffer)}

        @property
        def reads(self) -> list[str]:
            return []

        @property
        def writes(self) -> list[str]:
            return ["response"]

        def update(self, result: dict, state: State) -> State:
            return state.update(**result)

    action = SimpleStreamingAction()
    STR = "test streaming action"
    assert action.run(State({"echo": STR}))["response"] == STR


def sample_generator(chars: str) -> Generator[dict, None, Tuple[dict, State]]:
    buffer = []
    for c in chars:
        buffer.append(c)
        yield {"response": c}
    joined = "".join(buffer)
    return {"response": joined}, State({"response": joined})


def test_streaming_result_container_iterate():
    string_value = "test streaming action"
    container = StreamingResultContainer(
        sample_generator(string_value),
        initial_state=State(),
        process_result=lambda r, s: (r, s),
        callback=lambda s, r, e: None,
    )
    assert [item["response"] for item in list(container)] == list(string_value)
    result, state = container.get()
    assert result["response"] == string_value


def test_streaming_result_get_runs_through():
    string_value = "test streaming action"
    container = StreamingResultContainer(
        sample_generator(string_value),
        initial_state=State(),
        process_result=lambda r, s: (r, s),
        callback=lambda s, r, e: None,
    )
    result, state = container.get()
    assert result["response"] == string_value


def test_streaming_result_callback_called():
    called = []
    string_value = "test streaming action"

    container = StreamingResultContainer(
        sample_generator(string_value),
        # initial state is here solely for returning debugging so we can return an
        # state to the user in the case of failure
        initial_state=State({"foo": "bar"}),
        process_result=lambda r, s: (r, s),
        callback=lambda s, r, e: called.append((s, r, e)),
    )
    container.get()
    assert len(called) == 1
    state, result, error = called[0]
    assert result["response"] == string_value
    assert state["response"] == string_value
    assert error is None


def test_streaming_result_callback_error():
    """This tests whether the callback is called when an error occurs in the generator. Note that try/except
    blocks -- this is required so we can end up delegating to the generators closing capability"""

    class SentinelError(Exception):
        pass

    try:
        called = []
        string_value = "test streaming action"
        container = StreamingResultContainer(
            sample_generator(string_value),
            initial_state=State({"foo": "bar"}),
            process_result=lambda r, s: (r, s),
            callback=lambda r, s, e: called.append((r, s, e)),
        )
        try:
            next(container)
            raise SentinelError("error")
        finally:
            assert len(called) == 1
            ((result, state, error),) = called
            assert state["foo"] == "bar"
            assert result is None
            # Exception is currently not exactly what we want, so won't assert on that.
            # See note in StreamingResultContainer
    except SentinelError:
        pass
