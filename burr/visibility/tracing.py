import dataclasses
import functools
import inspect
import logging
import uuid
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from contextvars import ContextVar
from hashlib import sha256
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from burr.lifecycle.internal import LifecycleAdapterSet

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ActionSpan:
    action: str
    action_sequence_id: int
    name: str
    parent: Optional["ActionSpan"]
    sequence_id: int = 0
    child_count: int = 0

    def spawn(self, name: str) -> "ActionSpan":
        self.child_count += 1
        return ActionSpan(
            action=self.action,
            action_sequence_id=self.action_sequence_id,
            name=name,
            parent=self,
            sequence_id=self.child_count - 1,  # sequence id is 0 indexed
            child_count=0,  # start the child count at 0
        )

    @property
    def uid(self) -> str:
        action_sequence_id = self.action_sequence_id
        parent_ids = [self.sequence_id]
        current = self
        while (current := current.parent) is not None:
            parent_ids.append(current.sequence_id)

        return f"{action_sequence_id}:{'.'.join(reversed([str(x) for x in parent_ids]))}"

    @classmethod
    def create_initial(
        cls, action: str, name: str, sequence_id: int, action_sequence_id: int
    ) -> "ActionSpan":
        """Creates the initial action span for an action. This should be only called if the current
        action span is none.

        :param action:
        :param name:
        :param sequence_id:
        :return:
        """
        return ActionSpan(
            action=action,
            name=name,
            sequence_id=sequence_id,
            parent=None,
            action_sequence_id=action_sequence_id,
        )


execution_context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
    "execution_context",
    default=None,
)


def create_span_id() -> str:
    """Creates a unique

    :return:
    """
    return f"span_{str(uuid.uuid4())}"


class ActionSpanTracer(AbstractContextManager, AbstractAsyncContextManager):
    """Context manager for use within tracing actions. This has the role solely of delegating
    to hooks -- it does not do anything except manage context and pass those to the hooks.

    Note that a new instance of this will be passed to every action that is traced. This allows
    us to reset this based on state. This can handle both synchronous and asynchronous contexts.

    You will be using this through the action API. When you declare ``__tracer`` as a parameter,
    it gives you a callable that, when called with a span name, returns an `ActionSpanTracer`

    .. code-block:: python

        @action(reads=[...], writes=[...])
        def my_action(state: State, __tracer: TracerFactory) -> tuple[dict, State]:
            context_manager: ActionSpanTracer = __tracer("my_span_name")
            with context_manager:
                ...


    The following hooks are respected:

    - :py:class:`pre_span_start <burr.lifecycle.base.PreSpanStart>` and :py:class:`async pre_span_start <burr.lifecycle.base.PreSpanStartAsync>`
    - :py:class:`post_span_end <burr.lifecycle.base.PostSpanEnd>` and :py:class:`async post_span_end <burr.lifecycle.base.PostSpanEndAsync>`
    """

    def __init__(
        self,
        action: str,
        action_sequence_id: int,
        span_name: str,
        lifecycle_adapters: LifecycleAdapterSet,
        app_id: str,
        partition_key: Optional[str],
        span_dependencies: List[str],
        top_level_span_count: int = 0,
        context_var=execution_context_var,
    ):
        """Initialiezs the ActionSpanTracer.

        :param action:
        :param span_name:
        :param lifecycle_adapters:
        :param span_dependencies:
        :param top_level_span_count:
        """
        self.action = action
        self.action_sequence_id = action_sequence_id
        self.lifecycle_adapters = lifecycle_adapters
        self.span_name = span_name
        self.span_dependencies = span_dependencies
        self.top_level_span_count = top_level_span_count
        self.context_var = context_var
        self.app_id = app_id
        self.partition_key = partition_key

    def _sync_hooks_enter(self, context: ActionSpan):
        self.lifecycle_adapters.call_all_lifecycle_hooks_sync(
            "pre_start_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            action_sequence_id=self.action_sequence_id,
            app_id=self.app_id,
            partition_key=self.partition_key,
        )

    async def _async_hooks_enter(self, context: ActionSpan):
        await self.lifecycle_adapters.call_all_lifecycle_hooks_async(
            "pre_start_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            action_sequence_id=self.action_sequence_id,
            app_id=self.app_id,
            partition_key=self.partition_key,
        )

    async def _async_hooks_exit(self, context: ActionSpan):
        await self.lifecycle_adapters.call_all_lifecycle_hooks_async(
            "post_end_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            action_sequence_id=self.action_sequence_id,
            app_id=self.app_id,
            partition_key=self.partition_key,
        )

    def _enter(self):
        current_execution_context = self.context_var.get()
        if current_execution_context is None:
            # create an initial one if we're at the top level
            self.context_var.set(
                ActionSpan.create_initial(
                    self.action,
                    self.span_name,
                    self.top_level_span_count - 1,
                    action_sequence_id=self.action_sequence_id,
                )
            )
        else:
            self.context_var.set(current_execution_context.spawn(self.span_name))
        return self.context_var.get()

    def _exit(self):
        current_execution_context = self.context_var.get()
        self.context_var.set(current_execution_context.parent)
        return current_execution_context

    def _sync_hooks_exit(self, context: ActionSpan):
        self.lifecycle_adapters.call_all_lifecycle_hooks_sync(
            "post_end_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            action_sequence_id=self.action_sequence_id,
            app_id=self.app_id,
            partition_key=self.partition_key,
        )

    def __enter__(self):
        """Enters the context manager"""
        enter_context = self._enter()
        self._sync_hooks_enter(enter_context)
        return self

    def __exit__(
        self,
        __exc_type: Type[BaseException],
        __exc_value: Optional[Type[BaseException]],
        __traceback: Optional[Type[BaseException]],
    ) -> Optional[bool]:
        """Exits the context manager."""
        prior_execution_context = self._exit()
        self._sync_hooks_exit(prior_execution_context)
        return None

    def log_attribute(self, key: str, value: Any):
        """Logs a single attribute to the UI. Note that this must
        be paired with a tracker or a tracking hook to be useful, otherwise it
        will be a no-op.

        :param key: Name of the attribute (must be unique per action/span)
        :param value: Value of the attribute.
        """
        self.log_attributes(**{key: value})

    def log_attributes(self, **attributes):
        """Logs a set of attributes to the UI. Note that this must
        be paired with a tracker or a tracking hook to be useful, otherwise it
        will be a no-op.

        :param attributes: Attributes to log
        """
        self.lifecycle_adapters.call_all_lifecycle_hooks_sync(
            "do_log_attributes",
            attributes=attributes,
            action=self.action,
            action_sequence_id=self.action_sequence_id,
            span=self.context_var.get(),
            app_id=self.app_id,
            partition_key=self.partition_key,
            tags={},  # TODO -- add tags
        )

    async def __aenter__(self) -> "ActionSpanTracer":
        """Enters the context manager, async mode"""
        enter_context = self._enter()
        self._sync_hooks_enter(enter_context)
        await self._async_hooks_enter(self.context_var.get())
        return self

    async def __aexit__(
        self,
        __exc_type: Type[BaseException],
        __exc_value: Optional[Type[BaseException]],
        __traceback: Optional[Type[BaseException]],
    ) -> Optional[bool]:
        """Exits the context manager, async mode"""
        prior_execution_context = self._exit()
        self._sync_hooks_exit(prior_execution_context)
        await self._async_hooks_exit(prior_execution_context)
        return None


class TracerFactory(ActionSpanTracer):
    """Represents a tracer factory to create tracer instances. User never instantiates this
    directly. Rather, this gets injected by the application. This gives a new span.

    Note this carries state -- the top level span count. This is important for the sequence id
    at the root level.

    You will only ever see a tracer factory in the context of an action, passed through the `__tracer`
    parameter.

     .. code-block:: python

        @action(reads=[...], writes=[...])
        def my_action(state: State, __tracer: TracerFactory) -> tuple[dict, State]:
            context_manager: ActionSpanTracer = __tracer("my_span_name")
            with context_manager:
                ...
    """

    def __init__(
        self,
        action: str,
        sequence_id: int,
        app_id: str,
        partition_key: Optional[str],
        lifecycle_adapters: LifecycleAdapterSet,
        _context_var: ContextVar[Optional[ActionSpan]] = execution_context_var,
    ):
        """Instantiates a tracer factory.

        :param action: Action name
        :param lifecycle_adapters: Lifecycle adapters
        :param _context_var: Context var to use for the action span
        """
        super(TracerFactory, self).__init__(
            action=action,
            action_sequence_id=sequence_id,
            span_name="root",
            lifecycle_adapters=lifecycle_adapters,
            app_id=app_id,
            partition_key=partition_key,
            span_dependencies=[],
            top_level_span_count=0,
            context_var=_context_var,
        )

    def __call__(
        self, span_name: str, span_dependencies: Optional[List[str]] = None
    ) -> ActionSpanTracer:
        if self.context_var.get() is None:
            self.top_level_span_count += 1
        if span_dependencies is None:
            span_dependencies = []
        return ActionSpanTracer(
            action=self.action,
            action_sequence_id=self.action_sequence_id,
            span_name=span_name,
            lifecycle_adapters=self.lifecycle_adapters,
            span_dependencies=span_dependencies,
            context_var=self.context_var,
            top_level_span_count=self.top_level_span_count,
            app_id=self.app_id,
            partition_key=self.partition_key,
        )


FNType = TypeVar("FNType", bound=Callable)

# This is specifically meant to set anything that is "out of band" -- I.E.
# Through a decorator that does not have access to the parameter
# This is an internal API that we are liable to change over time
# This is set by the application on every `step` call

tracer_factory_context_var: ContextVar[Optional[TracerFactory]] = ContextVar(
    "tracer_context",
    default=None,
)


class trace:
    def __init__(
        self,
        capture_inputs: bool = True,
        capture_outputs: bool = True,
        input_filterlist: Optional[List[str]] = None,
        span_name: Optional[str] = None,
        _context_var: ContextVar[Optional[TracerFactory]] = tracer_factory_context_var,
    ):
        """trace() can wrap any function and uses the tracer to create a span and log
        attributes. This also (by default) logs the inputs/outputs of a function as attributes.
        Be careful not to include sensitive data in the inputs/outputs, but if you do, you have the
        input_filterlist to exclude it.

        This works with sync/async

        Take the following code:

        .. code-block:: python

            from burr.visibility import trace

            @trace()
            def call_llm(prompt):
                return _query(...)

            @trace()
            def generate_text(prompt: str) -> str:
                result = call_llm(prompt)
                return f"<p>{result}</p>"

            @action(reads=["prompt"], writes=["response"])
            def prompt_action(state: State) -> State:
                response = generate_text(state["prompt"])
                return state.update(response=response)

        Every time `prompt_action` is called (within the context of prompt_action), it will generate a trace that looks like the following:

        ------ prompt action --------------------------------------------
            ----- generate_text -----------------------------------
                ----- call_llm -----------------------------------

        If it is called outside the context of a Burr action, it will be effectively a no-op.


        :param capture_inputs: Whether to capture inputs as attributes (defaults to True).
            Note that this only works with keyword-argument bindable functions.
        :param capture_outputs: Whether to capture outputs as attributes (defaults to True)
        :param input_filterlist: A list of inputs to filter out (defaults to filtering nothing. Use if you have sensitive data)
        :param span_name: Name of the span, will default to the function name
        :param _context_var: Context var to use for the tracer factory, used purely for internal testing
        """
        self.capture_inputs = capture_inputs
        self.capture_outputs = capture_outputs
        self.input_filterlist = input_filterlist or []
        self.span_name = span_name
        self.context_var = _context_var

    def _ensure_bind(self, fn, *args, **kwargs) -> Dict[str, Any]:
        try:
            bound_params = inspect.signature(fn).bind(*args, **kwargs)
        except TypeError as e:
            func_name = fn.__name__
            raise TypeError(f"{func_name}: {e.args[0]}") from None

        bound_kwargs = bound_params.arguments
        return bound_kwargs

    def _get_auto_attributes(self, fn: FNType):
        qualname = fn.__qualname__
        try:
            code, *_ = inspect.getsourcelines(fn)
            code_hash = sha256("".join(code).encode()).hexdigest()
        except OSError:
            code_hash = "Unable to retrieve source code for hash"
        return {"__burr_function": qualname, "__burr_function_hash": code_hash}

    def _log_parameters(self, __action_span_tracer: ActionSpanTracer, bound_aprams):
        # TODO -- ensure we can serialize this
        filtered_params = {k: v for k, v in bound_aprams.items() if k not in self.input_filterlist}
        __action_span_tracer.log_attributes(**filtered_params)

    def _get_span_name(self, fn: FNType) -> str:
        return self.span_name if self.span_name else fn.__name__

    def __call__(self, fn: FNType) -> FNType:
        @functools.wraps(fn)
        def wrapped_fn(*args, **kwargs):
            tracer_factory = self.context_var.get()
            if tracer_factory is not None:
                bound_params = self._ensure_bind(fn, *args, **kwargs)
                with tracer_factory(self._get_span_name(fn)) as action_span_tracer:
                    if self.capture_inputs:
                        self._log_parameters(action_span_tracer, bound_params)
                    additional_attributes = self._get_auto_attributes(fn)
                    action_span_tracer.log_attributes(**additional_attributes)
                    output = fn(*args, **kwargs)
                    if self.capture_outputs:
                        action_span_tracer.log_attributes(**{"return": output})
                    return output
            logger.debug(
                f"Function: {fn.__name__} is decorated with @trace but is not being executed "
                f"in the context of a Burr action. No tracing will occur."
            )
            return fn(*args, **kwargs)

        @functools.wraps(fn)
        async def awrapped_fn(*args, **kwargs):
            tracer_factory = self.context_var.get()
            if tracer_factory is not None:
                bound_params = self._ensure_bind(fn, *args, **kwargs)
                with tracer_factory(self._get_span_name(fn)) as action_span_tracer:
                    if self.capture_inputs:
                        self._log_parameters(action_span_tracer, bound_aprams=bound_params)
                    additional_attributes = self._get_auto_attributes(fn)
                    action_span_tracer.log_attributes(**additional_attributes)
                    output = await fn(*args, **kwargs)
                    if self.capture_outputs:
                        action_span_tracer.log_attributes(**{"return": output})
                    return output
            logger.debug(
                f"Function: {fn.__name__} is decorated with @trace but is not being executed "
                f"in the context of a Burr action. No tracing will occur."
            )
            return await fn(*args, **kwargs)

        if inspect.iscoroutinefunction(fn):
            return awrapped_fn
        return wrapped_fn
