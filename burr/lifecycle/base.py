import abc
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    # type-checking-only for a circular import
    from burr.core import State, Action, ApplicationGraph
    from burr.visibility import ActionSpan

from burr.lifecycle.internal import lifecycle


@lifecycle.base_hook("pre_run_step")
class PreRunStepHook(abc.ABC):
    """Hook that runs before a step is executed"""

    @abc.abstractmethod
    def pre_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        inputs: Dict[str, Any],
        **future_kwargs: Any,
    ):
        """Run before a step is executed.

        :param state: State prior to step execution
        :param action: Action to be executed
        :param inputs: Inputs to the action
        :param sequence_id: Sequence ID of the action
        :param future_kwargs: Future keyword arguments
        """
        pass


@lifecycle.base_hook("pre_run_step")
class PreRunStepHookAsync(abc.ABC):
    """Async hook that runs before a step is executed"""

    @abc.abstractmethod
    async def pre_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        inputs: Dict[str, Any],
        **future_kwargs: Any,
    ):
        """Async run before a step is executed.

        :param state: State prior to step execution
        :param action: Action to be executed
        :param inputs: Inputs to the action
        :param sequence_id: Sequence ID of the action
        :param future_kwargs: Future keyword arguments
        """
        pass


@lifecycle.base_hook("post_run_step")
class PostRunStepHook(abc.ABC):
    """Hook that runs after a step is executed"""

    @abc.abstractmethod
    def post_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        result: Optional[Dict[str, Any]],
        exception: Exception,
        **future_kwargs: Any,
    ):
        """Run after a step is executed.

        :param state: State after step execution
        :param action: Action that was executed
        :param result: Result of the action
        :param sequence_id: Sequence ID of the action
        :param exception: Exception that was raised
        :param future_kwargs: Future keyword arguments
        """
        pass


@lifecycle.base_hook("post_run_step")
class PostRunStepHookAsync(abc.ABC):
    """Async hook that runs after a step is executed"""

    @abc.abstractmethod
    async def post_run_step(
        self,
        *,
        app_id: str,
        partition_key: str,
        sequence_id: int,
        state: "State",
        action: "Action",
        result: Optional[dict],
        exception: Exception,
        **future_kwargs: Any,
    ):
        """Async run after a step is executed

        :param state: State after step execution
        :param action: Action that was executed
        :param result: Result of the action
        :param sequence_id: Sequence ID of the action
        :param exception: Exception that was raised
        :param future_kwargs: Future keyword arguments
        """
        pass


@lifecycle.base_hook("post_application_create")
class PostApplicationCreateHook(abc.ABC):
    """Synchronous hook that runs post instantiation of an ``Application``
    object (after ``.build()`` is called on the ``ApplicationBuilder`` object.)"""

    @abc.abstractmethod
    def post_application_create(
        self,
        *,
        app_id: str,
        partition_key: Optional[str],
        state: "State",
        application_graph: "ApplicationGraph",
        **future_kwargs: Any,
    ):
        """Runs after an "application" object is instantiated. This is run by the Application, in its constructor,
        as the last step.

        :param app_id: Application ID
        :param partition_key: Partition key of application
        :param state: Current state of the application
        :param application_graph: Application graph of the application, representing the state machine
        :param future_kwargs: Future keyword arguments for backwards compatibility
        """
        pass


@lifecycle.base_hook("pre_start_span")
class PreStartSpanHook(abc.ABC):
    """Hook that runs before a span is started in the tracing API.
    This can be either a context manager or a logger of sorts."""

    @abc.abstractmethod
    def pre_start_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        pass


@lifecycle.base_hook("pre_start_span")
class PreStartSpanHookAsync(abc.ABC):
    @abc.abstractmethod
    async def pre_start_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        pass


@lifecycle.base_hook("post_end_span")
class PostEndSpanHook(abc.ABC):
    """Hook that runs after a span is ended in the tracing API.
    This can be either a context manager or a logger."""

    @abc.abstractmethod
    def post_end_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        pass


@lifecycle.base_hook("post_end_span")
class PostEndSpanHookAsync(abc.ABC):
    @abc.abstractmethod
    async def post_end_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        pass


# THESE ARE NOT IN USE
# TODO -- implement/decide how to use them
@lifecycle.base_hook("pre_run_application")
class PreRunApplicationHook(abc.ABC):
    @abc.abstractmethod
    def pre_run_application(
        self, *, app_id: str, partition_key: str, state: "State", **future_kwargs: Any
    ):
        pass


@lifecycle.base_hook("pre_run_application")
class PreRunApplicationHookAsync(abc.ABC):
    @abc.abstractmethod
    async def pre_run_application(
        self, *, app_id: str, partition_key: str, state: "State", **future_kwargs
    ):
        pass


@lifecycle.base_hook("post_run_application")
class PostRunApplicationHook(abc.ABC):
    @abc.abstractmethod
    def post_run_application(
        self,
        *,
        app_id: str,
        partition_key: str,
        state: "State",
        until: list[str],
        results: list[dict],
        **future_kwargs,
    ):
        pass


@lifecycle.base_hook("post_run_application")
class PostRunApplicationHookAsync(abc.ABC):
    @abc.abstractmethod
    async def post_run_application(
        self,
        *,
        app_id: str,
        partition_key: str,
        state: "State",
        until: list[str],
        results: list[dict],
        **future_kwargs,
    ):
        pass


# strictly for typing -- this conflicts a bit with the lifecycle decorator above, but its fine for now
# This makes IDE completion/type-hinting easier
LifecycleAdapter = Union[
    PreRunStepHook,
    PreRunStepHookAsync,
    PostRunStepHook,
    PostRunStepHookAsync,
    PreRunApplicationHook,
    PreRunApplicationHookAsync,
    PostRunApplicationHook,
    PostRunApplicationHookAsync,
    PostApplicationCreateHook,
    PreStartSpanHook,
    PreStartSpanHookAsync,
    PostEndSpanHook,
    PostEndSpanHookAsync,
]
