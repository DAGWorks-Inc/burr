import dataclasses
import uuid
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from contextvars import ContextVar
from typing import Any, List, Optional, Type

from burr.lifecycle.internal import LifecycleAdapterSet


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

    def _sync_hooks_enter(self, context: ActionSpan):
        self.lifecycle_adapters.call_all_lifecycle_hooks_sync(
            "pre_start_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            sequence_id=self.action_sequence_id,
        )

    async def _async_hooks_enter(self, context: ActionSpan):
        await self.lifecycle_adapters.call_all_lifecycle_hooks_async(
            "pre_start_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            sequence_id=self.action_sequence_id,
        )

    async def _async_hooks_exit(self, context: ActionSpan):
        await self.lifecycle_adapters.call_all_lifecycle_hooks_async(
            "post_end_span",
            action=self.action,
            span=context,
            span_dependencies=self.span_dependencies,
            sequence_id=self.action_sequence_id,
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
            sequence_id=self.action_sequence_id,
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

    def log_artifact(self, name: str, value: Any):
        raise NotImplementedError

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


class TracerFactory:
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
        lifecycle_adapters: LifecycleAdapterSet,
        _context_var: ContextVar[Optional[ActionSpan]] = execution_context_var,
    ):
        """Instantiates a tracer factory.

        :param action: Action name
        :param lifecycle_adapters: Lifecycle adapters
        :param _context_var: Context var to use for the action span
        """
        self.action = action
        self.lifecycle_adapters = lifecycle_adapters
        self.context_var = _context_var
        self.top_level_span_count = 0
        self.action_sequence_id = sequence_id

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
        )
