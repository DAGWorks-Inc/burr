from typing import Tuple

import pytest

from burr.core import State
from burr.core.action import (
    Action,
    Condition,
    Function,
    Result,
    _validate_action_function,
    action,
    create_action,
    default,
)


def test_is_async_true():
    class AsyncFunction(Function):
        def reads(self) -> list[str]:
            return []

        async def run(self, state: State) -> dict:
            return {}

    func = AsyncFunction()
    assert func.is_async()


def test_is_async_false():
    class SyncFunction(Function):
        def reads(self) -> list[str]:
            return []

        def run(self, state: State) -> dict:
            return {}

    func = SyncFunction()
    assert not func.is_async()


class _BasicAction(Action):
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
    action = _BasicAction()
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


def test_result():
    result = Result(fields=["foo", "bar"])
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


def test_create_action_class_api():
    raw_action = _BasicAction()
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
