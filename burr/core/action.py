import abc
import ast
import copy
import inspect
import types
from typing import Any, Callable, List, Protocol, Tuple, TypeVar, Union

from burr.core.state import State


class Function(abc.ABC):
    """Interface to represent the 'computing' part of an action"""

    @property
    @abc.abstractmethod
    def reads(self) -> list[str]:
        """Returns the keys from the state that this function reads

        :return: A list of keys
        """
        pass

    @abc.abstractmethod
    def run(self, state: State) -> dict:
        """Runs the function on the given state and returns the result.
        The result is jsut a key/value dictionary.

        :param state: State to run the function on
        :return: Result of the function
        """

    def is_async(self) -> bool:
        """Convenience method to check if the function is async or not.
        This can be used by the application to run it.

        :return: True if the function is async, False otherwise
        """
        return inspect.iscoroutinefunction(self.run)


class Reducer(abc.ABC):
    """Interface to represent the 'updating' part of an action"""

    @property
    @abc.abstractmethod
    def writes(self) -> list[str]:
        """Returns the keys from the state that this reducer writes

        :return: A list of keys
        """
        pass

    @abc.abstractmethod
    def update(self, result: dict, state: State) -> State:
        pass


class Action(Function, Reducer, abc.ABC):
    def __init__(self):
        """Represents an action in a state machine. This is the base class from which
        actions extend. Note that this class needs to have a name set after the fact.
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
        across your application."""
        return self._name

    def __repr__(self):
        read_repr = ", ".join(self.reads) if self.reads else "{}"
        write_repr = ", ".join(self.writes) if self.writes else "{}"
        return f"{self.name}: {read_repr} -> {write_repr}"


class Condition(Function):
    KEY = "PROCEED"

    def __init__(self, keys: List[str], resolver: Callable[[State], bool], name: str = None):
        """Base condition class. Chooses keys to read from the state and a resolver function.

        :param keys: Keys to read from the state
        :param resolver:  Function to resolve the condition to True or False
        :param name: Name of the condition
        """
        self._resolver = resolver
        self._keys = keys
        self._name = name

    @staticmethod
    def expr(expr: str) -> "Condition":
        """Returns a condition that evaluates the given expression. Expression must use
        only state variables and Python operators. Do not trust that anything else will work.

        Do not accept expressions generated from user-inputted text, this has the potential to be unsafe.

        You can also refer to this as ``from burr.core import expr`` in the API.

        :param expr: Expression to evaluate
        :return: A condition that evaluates the given expression
        """
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
        state and equal to the given values.

        You can also refer to this as ``from burr.core import when`` in the API.

        :param kwargs: Keyword arguments of keys and values to check -- will be an AND condition
        :return: A condition that checks if the given keys are in the state and equal to the given values
        """
        keys = list(kwargs.keys())

        def condition_func(state: State) -> bool:
            for key, value in kwargs.items():
                if state.get(key) != value:
                    return False
            return True

        name = f"{', '.join(f'{key}={value}' for key, value in sorted(kwargs.items()))}"
        return Condition(keys, condition_func, name=name)

    @classmethod
    @property
    def default(self) -> "Condition":
        """Returns a default condition that always resolves to True.
        You can also refer to this as ``from burr.core import default`` in the API.

        :return: A default condition that always resolves to True
        """
        return Condition([], lambda _: True, name="default")

    @property
    def name(self) -> str:
        return self._name


default = Condition.default
when = Condition.when
expr = Condition.expr


class Result(Action):
    def __init__(self, fields: list[str]):
        """Represents a result action. This is purely a convenience class to
        pull data from state and give it out to the result. It does nothing to
        the state itself.

        :param fields: Fields to pull from the state
        """
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


class FunctionBasedAction(Action):
    ACTION_FUNCTION = "action_function"

    def __init__(
        self,
        fn: Callable[..., Tuple[dict, State]],
        reads: List[str],
        writes: List[str],
        bound_params: dict = None,
    ):
        """Instantiates a function-based action with the given function, reads, and writes.
        The function must take in a state and return a tuple of (result, new_state).

        :param fn:
        :param reads:
        :param writes:
        """
        super(FunctionBasedAction, self).__init__()
        self._fn = fn
        self._reads = reads
        self._writes = writes
        self._state_created = None
        self._bound_params = bound_params if bound_params is not None else {}

    @property
    def fn(self) -> Callable:
        return self._fn

    @property
    def reads(self) -> list[str]:
        return self._reads

    def run(self, state: State) -> dict:
        result, new_state = self._fn(state, **self._bound_params)
        self._state_created = new_state
        return result

    @property
    def writes(self) -> list[str]:
        return self._writes

    def update(self, result: dict, state: State) -> State:
        if self._state_created is None:
            raise ValueError(
                "FunctionBasedAction.run must be called before FunctionBasedAction.update"
            )
        # TODO -- validate that all the keys are contained -- fix up subset to handle this
        # TODO -- validate that we've (a) written only to the write ones (by diffing the read ones),
        #  and (b) written to no more than the write ones
        return self._state_created.subset(*self._writes)

    def with_params(self, **kwargs: Any) -> "FunctionBasedAction":
        """Binds parameters to the function.
        Note that there is no reason to call this by the user. This *could*
        be done at the class level, but given that API allows for constructor parameters
        (which do the same thing in a cleaner way), it is best to keep it here for now.

        :param kwargs:
        :return:
        """
        new_action = copy.copy(self)
        new_action._bound_params = {**self._bound_params, **kwargs}
        return new_action


def _validate_action_function(fn: Callable):
    """Validates that an action has the signature: (state: State) -> Tuple[dict, State]

    :param fn: Function to validate
    """
    sig = inspect.signature(fn)
    params = sig.parameters
    if list(params.keys())[0] != "state" or not list(params.values())[0].annotation == State:
        raise ValueError(f"Function {fn} must take in a single argument: state with type: State")
    other_params = list(params.keys())[1:]
    for param in other_params:
        param = params[param]
        if param.kind not in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }:
            raise ValueError(
                f"Function {fn} has an invalid parameter: {param}. "
                f"All parameters must be position or keyword only,"
                f"so that bind(**kwargs) can be applied."
            )

    if sig.return_annotation != Tuple[dict, State]:
        raise ValueError(
            f"Function {fn} must return a tuple of (result, new_state), "
            f"not {sig.return_annotation}"
        )


C = TypeVar("C", bound=Callable)  # placeholder for any Callable


class FunctionRepresentingAction(Protocol[C]):
    action_function: FunctionBasedAction
    __call__: C

    def bind(self, **kwargs: Any):
        ...


def bind(self: FunctionRepresentingAction, **kwargs: Any) -> FunctionRepresentingAction:
    """Binds an action to the given parameters. This is functionally equivalent to
    functools.partial, but is more explicit and is meant to be used in the API. This only works with
    the functional API for ``@action`` and not with the class-based API.

    .. code-block:: python

        @action(["x"], ["y"])
        def my_action(state: State, z: int) -> Tuple[dict, State]:
            return {"y": state.get("x") + z}, state

        my_action.bind(z=2)

    :param self: The decorated function
    :param kwargs: The keyword arguments to bind
    :return: The decorated function with the given parameters bound
    """
    self.action_function = self.action_function.with_params(**kwargs)
    return self


def action(reads: List[str], writes: List[str]) -> Callable[[Callable], FunctionRepresentingAction]:
    """Decorator to create a function-based action. This is user-facing.
    Note that, in the future, with typed state, we may not need this for
    all cases.

    :param reads: Items to read from the state
    :param writes: Items to write to the state
    :return: The decorator to assign the function as an action
    """

    def decorator(fn) -> FunctionRepresentingAction:
        setattr(fn, FunctionBasedAction.ACTION_FUNCTION, FunctionBasedAction(fn, reads, writes))
        setattr(fn, "bind", types.MethodType(bind, fn))
        return fn

    return decorator


def create_action(action_: Union[Callable, Action], name: str) -> Action:
    """Factory function to create an action. This is meant to be called by
    the ApplicationBuilder, and not by the user. The internal API may change.

    :param action_: Object to create an action from
    :param name: The name to assign the action
    :return: An action with the given name
    """
    if hasattr(action_, FunctionBasedAction.ACTION_FUNCTION):
        action_ = getattr(action_, FunctionBasedAction.ACTION_FUNCTION)
    elif not isinstance(action_, Action):
        raise ValueError(
            f"Object {action_} is not a valid action. Have you decorated it with @action?"
        )
    return action_.with_name(name)
