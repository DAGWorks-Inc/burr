from burr.core import State
from burr.core.action import Action, Condition, Function, Result, default


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


def test_with_name():
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
