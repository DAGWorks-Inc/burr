import abc
import ast
import copy
import inspect
from typing import Callable, List

from burr.core.state import State


class Function(abc.ABC):
    @property
    @abc.abstractmethod
    def reads(self) -> list[str]:
        pass

    @abc.abstractmethod
    def run(self, state: State) -> dict:
        pass

    def is_async(self):
        return inspect.iscoroutinefunction(self.run)


class Reducer(abc.ABC):
    @property
    @abc.abstractmethod
    def writes(self) -> list[str]:
        pass

    @abc.abstractmethod
    def update(self, result: dict, state: State) -> State:
        pass


class Action(Function, Reducer, abc.ABC):
    def __init__(self):
        """Represents an action in a state machine. This is the base class from which:

        1. Custom actions
        2. Conditions
        3. Results

        All extend this class. Note that name is optional so that APIs can set the
        name on these actions as part of instantiation.
        When they're used, they must have a name set.
        """
        self._name = None

    def with_name(self, name: str) -> "Action":
        """Returns a copy of the given action with the given name. Why do we need this?
        We instantiate actions without names, and then set them later. This is a way to
        make the API cleaner/consolidate it, and the ApplicationBuilder will end up handling it
        for you, in the with_actions(...) method, which is the only way to use actions.

        Note they can also take in names in the constructor for testing, but otherwise this is
        not something users will ever have to think about.

        :param name: Name to set
        :return: A new action with the given name
        """
        if self._name is not None:
            raise ValueError(
                f"Name of {self} already set to {self._name} -- cannot set name to {name}"
            )
        # TODO -- ensure that we're not mutating anything later on
        # If we are, we may want to copy more intelligently
        new_action = copy.copy(self)
        new_action._name = name
        return new_action

    @property
    def name(self) -> str:
        """Gives the name of this action. This should be unique
        across your agent."""
        return self._name

    def __repr__(self):
        read_repr = ", ".join(self.reads) if self.reads else "{}"
        write_repr = ", ".join(self.writes) if self.writes else "{}"
        return f"{self.name}: {read_repr} -> {write_repr}"


class Condition(Function):
    KEY = "PROCEED"

    def __init__(self, keys: List[str], resolver: Callable[[State], bool], name: str = None):
        self._resolver = resolver
        self._keys = keys
        self._name = name

    @staticmethod
    def expr(expr: str) -> "Condition":
        """Returns a condition that evaluates the given expression"""
        tree = ast.parse(expr, mode="eval")

        # Visitor class to collect variable names
        class NameVisitor(ast.NodeVisitor):
            def __init__(self):
                self.names = set()

            def visit_Name(self, node):
                self.names.add(node.id)

        # Visit the nodes and collect variable names
        visitor = NameVisitor()
        visitor.visit(tree)
        keys = list(visitor.names)

        # Compile the expression into a callable function
        def condition_func(state: State) -> bool:
            __globals = state.get_all()  # we can get all becuase externally we will subset
            return eval(compile(tree, "<string>", "eval"), {}, __globals)

        return Condition(keys, condition_func, name=expr)

    def run(self, state: State) -> dict:
        return {Condition.KEY: self._resolver(state)}

    @property
    def reads(self) -> list[str]:
        return self._keys

    @classmethod
    def when(cls, **kwargs):
        """Returns a condition that checks if the given keys are in the
        state and equal to the given values."""
        keys = list(kwargs.keys())

        def condition_func(state: State) -> bool:
            for key, value in kwargs.items():
                if state.get(key) != value:
                    return False
            return True

        name = f"{', '.join(f'{key}={value}' for key, value in sorted(kwargs.items()))}"
        return Condition(keys, condition_func, name=name)

    @property
    def name(self) -> str:
        return self._name


default = Condition([], lambda _: True, name="default")
when = Condition.when
expr = Condition.expr


class Result(Action):
    def __init__(self, fields: list[str]):
        super(Result, self).__init__()
        self._fields = fields

    def run(self, state: State) -> dict:
        return {key: value for key, value in state.get_all().items() if key in self._fields}

    def update(self, result: dict, state: State) -> State:
        return state  # does not modify state in any way

    @property
    def reads(self) -> list[str]:
        return self._fields

    @property
    def writes(self) -> list[str]:
        return []
