import abc
import ast
import builtins
import copy
import inspect
import sys
import types
import typing
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
)

if sys.version_info <= (3, 11):
    Self = Any
else:
    from typing import Self

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
    def run(self, state: State, **run_kwargs) -> dict:
        """Runs the function on the given state and returns the result.
        The result is just a key/value dictionary.

        :param state: State to run the function on
        :param run_kwargs: Additional arguments to the function passed at runtime.
        :return: Result of the function
        """
        pass

    @property
    def inputs(self) -> Union[list[str], tuple[list[str], list[str]]]:
        """Represents inputs that are used for this to run.
        These correspond to the ``**run_kwargs`` in `run` above.

        Note that this has two possible return values:
        1. A list of strings -- these are the keys that are required to run the function
        2. A tuple of two lists of strings -- the first list is the required keys, the second is the optional keys

        :return: Either a list of strings (required inputs) or a tuple of two lists of strings (required and optional inputs)
        """
        return []

    @property
    def optional_and_required_inputs(self) -> tuple[set[str], set[str]]:
        """Returns a tuple of two lists of strings -- the first list is the required keys, the second is the optional keys.
        This is internal and not meant to override.

        :return: Tuple of required keys and optional keys
        """
        inputs = self.inputs
        if isinstance(inputs, tuple):
            return set(inputs[0]), set(inputs[1])
        return set(inputs), set()

    def validate_inputs(self, inputs: Optional[Dict[str, Any]]) -> None:
        """Validates the inputs to the function. This is a convenience method
        to allow for validation of inputs before running the function.

        :param inputs: Inputs to validate
        :raises ValueError: If the inputs are invalid
        """
        if inputs is None:
            inputs = {}
        required_inputs, optional_inputs = self.optional_and_required_inputs
        given_inputs = set(inputs.keys())
        missing_inputs = required_inputs - given_inputs
        additional_inputs = given_inputs - required_inputs - optional_inputs
        if missing_inputs or additional_inputs:
            raise ValueError(
                f"Inputs to function {self} are invalid. "
                + f"Missing the following inputs: {', '.join(missing_inputs)}."
                if missing_inputs
                else "" f"Additional inputs: {','.join(additional_inputs)}."
                if additional_inputs
                else ""
            )

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
        """Returns the keys from the state that this reducer writes.

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

    def with_name(self, name: str) -> Self:
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

    @property
    def single_step(self) -> bool:
        return False

    @property
    def streaming(self) -> bool:
        return False

    def get_source(self) -> str:
        """Returns the source code of the action. This will default to
        the source code of the class in which the action is implemented,
        but can be overwritten." Override if you want debugging/tracking
        to display a different source"""
        return inspect.getsource(self.__class__)

    def __repr__(self):
        read_repr = ", ".join(self.reads) if self.reads else "{}"
        write_repr = ", ".join(self.writes) if self.writes else "{}"
        return f"{self.name}: {read_repr} -> {write_repr}"


class Condition(Function):
    KEY = "PROCEED"

    def __init__(self, keys: List[str], resolver: Callable[[State], bool], name: str = None):
        """Base condition class. Chooses keys to read from the state and a resolver function.

        Note that you can use a few fundamental operators to build more complex conditions:

         - ``~`` operator allows you to automatically invert the condition.
         - ``|`` operator allows you to OR two conditions together.
         - ``&`` operator allows you to AND two conditions together.

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
        all_builtins = builtins.__dict__

        # Visitor class to collect variable names
        class NameVisitor(ast.NodeVisitor):
            def __init__(self):
                self.names = set()

            def visit_Name(self, node):
                if node.id not in all_builtins:
                    self.names.add(node.id)

        # Visit the nodes and collect variable names
        visitor = NameVisitor()
        visitor.visit(tree)
        keys = list(visitor.names)

        # Compile the expression into a callable function
        def condition_func(state: State) -> bool:
            __globals = state.get_all()  # we can get all because externally we will subset
            return eval(compile(tree, "<string>", "eval"), {}, __globals)

        return Condition(keys, condition_func, name=expr)

    def _validate(self, state: State):
        missing_keys = set(self._keys) - set(state.keys())
        if missing_keys:
            raise ValueError(
                f"Missing keys in state required by condition: {self} {', '.join(missing_keys)}"
            )

    def run(self, state: State, **run_kwargs) -> dict:
        self._validate(state)
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

    def __repr__(self):
        return f"condition: {self._name}"

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

    def __or__(self, other: "Condition") -> "Condition":
        """Combines two conditions with an OR operator. This will return a new condition
        that is the OR of the two conditions.

        To check if either foo is bar or baz is qux:

        .. code-block:: python

            condition = Condition.when(foo="bar") | Condition.when(baz="qux")

        :param other: Other condition to OR with
        :return: A new condition that is the OR of the two conditions
        """
        if not isinstance(other, Condition):
            raise ValueError(f"Cannot OR a Condition with {other}")
        return Condition(
            self._keys + other._keys,
            lambda state: self._resolver(state) or other.resolver(state),
            name=f"{self._name} | {other._name}",
        )

    def __and__(self, other: "Condition") -> "Condition":
        """Combines two conditions with an AND operator. This will return a new condition
        that is the AND of the two conditions.

        To check if both foo is bar and baz is qux:

        .. code-block:: python

            condition = Condition.when(foo="bar") & Condition.when(baz="qux")
            # equivalent to
            condition = Condition.when(foo="bar", baz="qux")

        :param other: Other condition to AND with
        :return:  A new condition that is the AND of the two conditions
        """
        if not isinstance(other, Condition):
            raise ValueError(f"Cannot AND a Condition with {other}")
        return Condition(
            self._keys + other._keys,
            lambda state: self._resolver(state) and other.resolver(state),
            name=f"{self._name} & {other._name}",
        )

    @property
    def resolver(self) -> Callable[[State], bool]:
        return self._resolver

    def __invert__(self):
        return Condition(self._keys, lambda state: not self._resolver(state), name=f"~{self._name}")


# Annotated inline as linters don't understand classmethods + properties
# These, however, are allowed up until python 3.13
# We're only keeping them as methods for documentation
# TODO -- remove the static methods and make them
default: Condition = Condition.default
when: Condition = Condition.when
expr: Condition = Condition.expr


class Result(Action):
    def __init__(self, *fields: str):
        """Represents a result action. This is purely a convenience class to
        pull data from state and give it out to the result. It does nothing to
        the state itself.

        :param fields: Fields to pull from the state and put into results
        """
        super(Result, self).__init__()
        self._fields = fields

    def run(self, state: State) -> dict:
        return {key: value for key, value in state.get_all().items() if key in self._fields}

    def update(self, result: dict, state: State) -> State:
        return state  # does not modify state in any way

    @property
    def reads(self) -> list[str]:
        return list(self._fields)

    @property
    def writes(self) -> list[str]:
        return []


class Input(Action):
    def __init__(self, *fields: str):
        """Represents an input action -- this reads something from an input
        then writes that directly to state. This is a convenience class for when you don't
        need to process the input and just want to put it in state for later use.

        :param fields: Fields to pull from the inputs and put into state
        """
        super(Input, self).__init__()
        self._fields = fields

    @property
    def reads(self) -> list[str]:
        return []  # nothing from state

    def run(self, state: State, **run_kwargs) -> dict:
        return {key: run_kwargs[key] for key in self._fields}

    @property
    def writes(self) -> list[str]:
        return list(self._fields)

    @property
    def inputs(self) -> list[str]:
        return list(self._fields)

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


class SingleStepAction(Action, abc.ABC):
    """Internal representation of a "single-step" action. While most actions will have
    a run and an update, this is a convenience class for actions that return them both at the same time.
    Note this is not user-facing, as the internal API is meant to change. This is largely special-cased
    for the function-based action, which users will not be extending.

    Currently this keeps a cache of the state created, which is not ideal. This is a temporary
    measure to make the API work, and will be removed in the future.
    """

    def __init__(self):
        super(SingleStepAction, self).__init__()
        self._state_created = None

    @property
    def single_step(self) -> bool:
        return True

    @abc.abstractmethod
    def run_and_update(self, state: State, **run_kwargs) -> tuple[dict, State]:
        """Performs a run/update at the same time.

        :param state: State to run the action on
        :param run_kwargs: Additional arguments to the function passed at runtime.
        :return: Result of the action and the new state
        """
        pass

    def run(self, state: State) -> dict:
        """This should never really get called.
        That said, this is an action so we have this in for now.
        TODO -- rethink the hierarchy. This is not user-facing, so its OK to change,
        and there's a bug we want to fix that requires this.

        :param state:
        :return:
        """
        raise ValueError(
            "SingleStepAction.run should never be called independently -- use run_and_update instead."
        )

    def update(self, result: dict, state: State) -> State:
        """Same with the above"""
        raise ValueError(
            "SingleStepAction.update should never be called independently -- use run_and_update instead."
        )

    def is_async(self) -> bool:
        """Convenience method to check if the function is async or not.
        We'll want to clean up the class hierarchy, but this is all internal.
        See note on ``run`` and ``update`` above

        :return: True if the function is async, False otherwise
        """
        return inspect.iscoroutinefunction(self.run_and_update)


# the following exist to share implementation between FunctionBasedStreamingAction and FunctionBasedAction
# TODO -- think through the class hierarchy to simplify, for now this is OK
def _get_inputs(bound_params: dict, fn: Callable) -> tuple[list[str], list[str]]:
    sig = inspect.signature(fn)
    required_inputs, optional_inputs = [], []
    for param_name, param in sig.parameters.items():
        if param_name != "state" and param_name not in bound_params:
            if param.default is inspect.Parameter.empty:
                # has no default means its required
                required_inputs.append(param_name)
            else:
                # has a default means its optional
                optional_inputs.append(param_name)
    return required_inputs, optional_inputs


FunctionBasedActionType = TypeVar(
    "FunctionBasedActionType", bound=Union["FunctionBasedAction", "FunctionBasedStreamingAction"]
)


class FunctionBasedAction(SingleStepAction):
    ACTION_FUNCTION = "action_function"

    def __init__(
        self,
        fn: Callable,
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
        self._bound_params = bound_params if bound_params is not None else {}
        self._inputs = _get_inputs(self._bound_params, self._fn)

    @property
    def fn(self) -> Callable:
        return self._fn

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def inputs(self) -> tuple[list[str], list[str]]:
        return self._inputs

    def with_params(self, **kwargs: Any) -> "FunctionBasedAction":
        """Binds parameters to the function.
        Note that there is no reason to call this by the user. This *could*
        be done at the class level, but given that API allows for constructor parameters
        (which do the same thing in a cleaner way), it is best to keep it here for now.

        :param kwargs:
        :return:
        """
        return FunctionBasedAction(
            self._fn, self._reads, self._writes, {**self._bound_params, **kwargs}
        )

    def run_and_update(self, state: State, **run_kwargs) -> tuple[dict, State]:
        return self._fn(state, **self._bound_params, **run_kwargs)

    def is_async(self) -> bool:
        return inspect.iscoroutinefunction(self._fn)

    def get_source(self) -> str:
        """Return the source of the code for this action."""
        return inspect.getsource(self._fn)


StreamType = Tuple[dict, Optional[State]]

GeneratorReturnType = Generator[StreamType, None, None]
AsyncGeneratorReturnType = AsyncGenerator[StreamType, None]

StreamingFn = Callable[..., GeneratorReturnType]
StreamingFnAsync = Callable[..., AsyncGeneratorReturnType]


class StreamingAction(Action, abc.ABC):
    """Base class for Streaming action. These are "multi-step", meaning that
    they run in multiple passes (run -> update)"""

    @abc.abstractmethod
    def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, None]:
        """Streaming action ``stream_run`` is different than standard action run. It:
        1. streams in an intermediate result (the dict output)
        2. yields the final result at the end

        Note that the user, in this case, is responsible for joining the result.

        For instance, you could have:

        .. code-block:: python

            def stream_run(state: State) -> Generator[dict, None, dict]:
                buffer = [] # you might want to be more efficient than simple strcat
                for token in query(state['prompt']):
                    yield {'response' : token}
                    buffer.append(token)
                yield {'response' : "".join(buffer)}

        This would utilize a simple string buffer (implemented by a list) to store the results
        and then join them at the end. We return the final result.

        :param state: State to run the action on
        :param run_kwargs: parameters passed to the run function -- these are specified by `inputs`
        :return: A generator that streams in a result and returns the final result
        """
        pass

    def run(self, state: State, **run_kwargs) -> dict:
        """Runs the streaming action through to completion."""
        gen = self.stream_run(state, **run_kwargs)
        last_result = None
        for item in gen:
            last_result = item
        return last_result

    @property
    def streaming(self) -> bool:
        return True


class AsyncStreamingAction(Action, abc.ABC):
    """Asynchronous version of the streaming action. This is a base class for streaming actions.
    Currently this is separate from the synchronous version, but we may want to merge them in the future.
    Note this is the "multi-step" variant, in which run/update are separate."""

    @abc.abstractmethod
    async def stream_run(self, state: State, **run_kwargs) -> AsyncGenerator[dict, None]:
        """Asynchronous streaming action ``stream_run`` is different than the standard action run. It:
        1. streams in an intermediate result (the dict output)
        2. yields the final result at the end

        Note that the user, in this case, is responsible for joining the result.

        For instance, you could have:

        .. code-block:: python

            async def stream_run(state: State) -> Generator[dict, None, dict]:
                buffer = [] # you might want to be more efficient than simple strcat
                async for token in query(state['prompt']): # asynchronous generator
                    yield {'response' : token}
                    buffer.append(token)
                yield {'response' : "".join(buffer)}

        This would utilize a simple string buffer (implemented by a list) to store the results
        and then join them at the end. We return the final result.

        :param state: State to run the action on
        :param run_kwargs: parameters passed to the run function -- these are specified by `inputs`
        :return: A generator that streams in a result and returns the final result
        """
        pass

    async def run(self, state: State, **run_kwargs) -> dict:
        """Runs the streaming action through to completion.
        Returns the final result. This is used if we want a streaming action
        as an intermediate.

        :param state: State to run the action on
        :param run_kwargs: Additional arguments to the function passed at runtime.
        :return: Final result
        """
        gen = self.stream_run(state, **run_kwargs)
        result = None
        async for item in gen:
            result = item
        return result

    @property
    def streaming(self) -> bool:
        return True

    def is_async(self) -> bool:
        return True


# TODO -- documentation for this
class StreamingResultContainer(Iterator[dict]):
    """Container for a streaming result. This allows you to:

    1. Iterate over the result as it comes in
    2. Get the final result/state at the end

    If you're familiar with generators/iterators in python, this is effectively an
    iterator that caches the final result after calling it. This is meant to be used
    exclusively with the streaming action calls in `Application`. Note that you will
    never instantiate this class directly, but you will use it in the API when it is returned
    by :py:meth:`stream_result <burr.core.application.Application.stream_result>`.
    For reference, here's how you would use it:

    .. code-block:: python

        action_we_just_ran, streaming_result_container = application.stream_result(...)
        print(f"getting streaming results for action={action_we_just_ran.name}")

        for result_component in streaming_result_container:
            print(result_component['response']) # this assumes you have a response key in your result

        final_result, final_state = streaming_result_container.get()
    """

    @staticmethod
    def pass_through(results: dict, final_state: State) -> "StreamingResultContainer":
        """Instantiates a streaming result container that just passes through the given results
        This is to be used internally -- it allows us to wrap non-streaming action results in a streaming
        result container."""

        def empty_generator() -> GeneratorReturnType:
            yield results, final_state

        return StreamingResultContainer(
            empty_generator(),
            final_state,
            lambda result, state: (result, state),
            lambda result, state, exc: None,
        )

    def __init__(
        self,
        streaming_result_generator: GeneratorReturnType,
        initial_state: State,
        process_result: Callable[[dict, State], tuple[dict, State]],
        callback: Callable[[Optional[dict], State, Optional[Exception]], None],
    ):
        """Initializes a streaming result container. User will never call directly.

        :param streaming_result_generator: Generator of streaming results. Note that this
            will always yield result, Optional[State] -- regardless of the API used to create it.
        :param initial_state:  The initial state
        :param process_result:  Function to process the result -- this gets called after the generator is exhausted,
            prior to returning the final result
        :param callback: Callback to call at the very end. This will only get called *once*, and will be called during the finally block of the generator
        """
        self.streaming_result_generator = streaming_result_generator
        self._action = action
        self._callback = callback
        self._process_result = process_result
        self._initial_state = initial_state
        self._result = None
        self._callback_realized = False

    def __next__(self):
        if self._result is not None:
            # we're done, and we've run through it
            raise StopIteration
        result, state = self.streaming_result_generator.__next__()
        if state is not None:  # we're done -- we've hit the last one
            self._result = self._process_result(result, state)
            raise StopIteration
        return result

    def __iter__(self):
        def gen_fn():
            try:
                while True:
                    out = self.__next__()
                    yield out
            except StopIteration:
                return
            finally:
                if self._result is None:
                    self._result = None, self._initial_state
                if not self._callback_realized:
                    exc = sys.exc_info()[1]
                    self._callback_realized = True
                    self._callback(*self._result, exc)

        # We really don't need an internal generator function but this was done to keep it the same
        # as the async version
        return gen_fn()

    def get(self) -> StreamType:
        # exhaust the generator
        for _ in self:
            pass

        return self._result


class AsyncStreamingResultContainer(typing.AsyncIterator[dict]):
    """Container for an async streaming result. This allows you to:
    1. Iterate over the result as it comes in
    2. Await the final result/state at the end

    If you're familiar with generators/iterators in python, this is effectively an
    iterator that caches the final result after calling it. This is meant to be used
    exclusively with the streaming action calls in `Application`. Note that you will
    never instantiate this class directly, but you will use it in the API when it is returned
    by :py:meth:`astream_result <burr.core.application.Application.stream_result>`.
    For reference, here's how you would use it:

    .. code-block:: python

        action_we_just_ran, streaming_result_container = await application.stream_result(...)
        print(f"getting streaming results for action={action_we_just_ran.name}")

        async for result_component in streaming_result_container:
            print(result_component['response']) # this assumes you have a response key in your result

        final_result, final_state = await streaming_result_container.get()
    """

    def __init__(
        self,
        streaming_result_generator: AsyncGeneratorReturnType,
        initial_state: State,
        process_result: Callable[[dict, State], tuple[dict, State]],
        callback: Callable[
            [Optional[dict], State, Optional[Exception]], typing.Coroutine[None, None, None]
        ],
    ):
        """Initializes an async streaming result container. User will never call directly.

        :param streaming_result_generator: Generator of streaming results. Note that this
            will always yield result, Optional[State] -- regardless of the API used to create it.
        :param initial_state:  The initial state
        :param process_result:  Function to process the result -- this gets called after the generator is exhausted,
            prior to returning the final result
        :param callback: Callback to call at the very end. This will only get called *once*, and will be called during the finally block of the generator
        """
        self.streaming_result_generator = streaming_result_generator
        self._initial_state = initial_state
        self._process_result = process_result
        self._callback = callback
        self._result = None
        self._callback_realized = False

    async def __anext__(self):
        """Moves to the next state in the streaming result"""
        if self._result is not None:
            # we're done, and we've run through it
            raise StopAsyncIteration
        result, state = await self.streaming_result_generator.__anext__()
        if state is not None:  # we're done -- we've hit the last one
            self._result = self._process_result(result, state)
            raise StopAsyncIteration
        return result

    def __aiter__(self):
        """Gives the iterator. Just calls anext, assigning the result in the finally block.
        Note this may not be perfect due to the complexity of callbacks for async generators,
        but it works in most cases."""

        async def gen_fn():
            try:
                while True:
                    yield await self.__anext__()
            except StopAsyncIteration:
                return
            finally:
                if self._result is None:
                    self._result = None, self._initial_state
                if not self._callback_realized:
                    exc = sys.exc_info()[1]
                    self._callback_realized = True
                    await self._callback(*self._result, exc)

        # return it as `__aiter__` cannot be async/have awaits :/
        return gen_fn()

    async def get(self) -> tuple[Optional[dict], State]:
        # exhaust the generator
        async for _ in self:
            pass

        return self._result

    @staticmethod
    def pass_through(results: dict, final_state: State) -> "AsyncStreamingResultContainer":
        """Creates a streaming result container that just passes through the given results.
        This is not a public facing API."""

        async def just_results() -> AsyncGeneratorReturnType:
            yield results, final_state

        async def empty_callback(result: Optional[dict], state: State, exc: Optional[Exception]):
            pass

        return AsyncStreamingResultContainer(
            just_results(), final_state, lambda result, state: (result, state), empty_callback
        )


class SingleStepStreamingAction(SingleStepAction, abc.ABC):
    """Class to represent a "single-step" streaming action. This is meant to
    work with the functional API. Note this is not user-facing -- the user will
    only interact with this by using the ``@streaming_action`` decorator.
    """

    @abc.abstractmethod
    def stream_run_and_update(
        self, state: State, **run_kwargs
    ) -> Union[GeneratorReturnType, AsyncGeneratorReturnType]:
        """Streaming version of the run and update function. This
        return type is a generator that streams in a result, has no "send"
        value, and returns the final result (new result + state).
        """
        pass

    def _run_and_update(self, state: State, **run_kwargs) -> tuple[dict, State]:
        gen = self.stream_run_and_update(state, **run_kwargs)
        result = None
        new_state = state
        for result, new_state in gen:
            pass
        # TODO -- validate that it has a single length output
        return result, new_state

    async def _arun_and_update(self, state: State, **run_kwargs) -> tuple[dict, State]:
        gen = self.stream_run_and_update(state, **run_kwargs)
        last_result = None
        new_state = state
        async for last_result, new_state in gen:
            pass
        return last_result, new_state

    def run_and_update(
        self, state: State, **run_kwargs
    ) -> Union[tuple[dict, State], Coroutine[Any, Any, tuple[dict, State]]]:
        """Runs the action and returns the final result. This allows us to run this as a
        single step action. This is helpful for when the streaming result needs to be
        run as an intermediate."""
        if self.is_async():
            return self._arun_and_update(state, **run_kwargs)
        return self._run_and_update(state, **run_kwargs)

    @property
    def streaming(self) -> bool:
        return True

    def is_async(self) -> bool:
        return inspect.isasyncgenfunction(self.stream_run_and_update)


class FunctionBasedStreamingAction(SingleStepStreamingAction):
    _fn: Union[StreamingFn, StreamingFnAsync]

    def __init__(
        self,
        fn: Union[
            StreamingFn,
            StreamingFnAsync,
        ],
        reads: List[str],
        writes: List[str],
        bound_params: dict = None,
    ):
        """Instantiates a function-based streaming action with the given function, reads, and writes.
        The function must take in a state (and inputs) and return a generator of (result, new_state).

        :param fn: Function to use
        :param reads:
        :param writes:
        """
        super(FunctionBasedStreamingAction, self).__init__()
        self._fn = fn
        self._reads = reads
        self._writes = writes
        self._bound_params = bound_params if bound_params is not None else {}

    async def _a_stream_run_and_update(
        self, state: State, **run_kwargs
    ) -> AsyncGeneratorReturnType:
        async for result in self._fn(state, **self._bound_params, **run_kwargs):
            yield result

    def _stream_run_and_update(self, state: State, **run_kwargs) -> GeneratorReturnType:
        yield from self._fn(state, **self._bound_params, **run_kwargs)

    def stream_run_and_update(
        self, state: State, **run_kwargs
    ) -> Union[AsyncGeneratorReturnType, GeneratorReturnType]:
        if self.is_async():
            return self._a_stream_run_and_update(state, **run_kwargs)
        return self._stream_run_and_update(state, **run_kwargs)

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def streaming(self) -> bool:
        return True

    def with_params(self, **kwargs: Any) -> "FunctionBasedStreamingAction":
        """Binds parameters to the function. This is not user-facing -- this is
        meant to be used internally by the API.

        :param kwargs:
        :return:
        """
        return FunctionBasedStreamingAction(
            self._fn, self._reads, self._writes, {**self._bound_params, **kwargs}
        )

    @property
    def inputs(self) -> tuple[list[str], list[str]]:
        return _get_inputs(self._bound_params, self._fn)

    @property
    def fn(self) -> Union[StreamingFn, StreamingFnAsync]:
        return self._fn

    def is_async(self) -> bool:
        return inspect.isasyncgenfunction(self._fn)

    def get_source(self) -> str:
        """Return the source of the code for this action"""
        return inspect.getsource(self._fn)


C = TypeVar("C", bound=Callable)  # placeholder for any Callable


class FunctionRepresentingAction(Protocol[C]):
    action_function: FunctionBasedActionType
    __call__: C

    def bind(self, **kwargs: Any) -> Self:
        ...


def bind(self: FunctionRepresentingAction, **kwargs: Any) -> FunctionRepresentingAction:
    """Binds an action to the given parameters. This is functionally equivalent to
    functools.partial, but is more explicit and is meant to be used in the API. This only works with
    the :py:meth:`@action <burr.core.action.action>`  functional API and not with the class-based API.

    .. code-block:: python

        @action(["x"], ["y"])
        def my_action(state: State, z: int) -> tuple[dict, State]:
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

    If parameters are not bound, they will be interpreted as inputs and must
    be passed in at runtime. If they have default values, they will be recorded
    as optional inputs. These can (optionally) be provided at runtime.

    :param reads: Items to read from the state
    :param writes: Items to write to the state
    :return: The decorator to assign the function as an action
    """

    def decorator(fn) -> FunctionRepresentingAction:
        setattr(fn, FunctionBasedAction.ACTION_FUNCTION, FunctionBasedAction(fn, reads, writes))
        setattr(fn, "bind", types.MethodType(bind, fn))
        return fn

    return decorator


def streaming_action(
    reads: List[str], writes: List[str]
) -> Callable[[Callable], FunctionRepresentingAction]:
    """Decorator to create a streaming function-based action. This is user-facing.

    If parameters are not bound, they will be interpreted as inputs and must be passed in at runtime.

    See the following example for how to use this decorator -- this reads ``prompt`` from the state and writes
    ``response`` back out, yielding all intermediate chunks.

    Note that this *must* return a value. If it does not, we will not know how to update the state, and
    we will error out.

    .. code-block:: python

        @streaming_action(reads=["prompt"], writes=['response'])
        def streaming_response(state: State) -> Generator[dict, None, tuple[dict, State]]:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{
                    'role': 'user',
                    'content': state["prompt"]
                    }],
                temperature=0,
            )
            buffer = []
            for chunk in response:
                delta = chunk.choices[0].delta.content
                buffer.append(delta)
                # yield partial results
                yield {'response': delta}
            full_response = ''.join(buffer)
            # return the final result
            return {'response': full_response}, state.update(response=full_response)

    """

    def wrapped(fn) -> FunctionRepresentingAction:
        setattr(
            fn,
            FunctionBasedAction.ACTION_FUNCTION,
            FunctionBasedStreamingAction(fn, reads, writes),
        )
        setattr(fn, "bind", types.MethodType(bind, fn))
        return fn

    return wrapped


ActionT = TypeVar("ActionT", bound=Action)


def create_action(action_: Union[Callable, ActionT], name: str) -> ActionT:
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
            f"Object {action_} is not a valid action. Have you decorated it with @action or @streaming_action?"
        )
    return action_.with_name(name)
