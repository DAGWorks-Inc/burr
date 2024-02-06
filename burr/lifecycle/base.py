import abc
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    # type-checking-only for a circular import
    from burr.core import State, Action

from burr.lifecycle.internal import lifecycle


@lifecycle.base_hook("pre_run_step")
class PreRunStepHook(abc.ABC):
    @abc.abstractmethod
    def pre_run_step(self, *, state: "State", action: "Action", **future_kwargs: Any):
        pass


@lifecycle.base_hook("pre_run_step")
class PreRunStepHookAsync(abc.ABC):
    @abc.abstractmethod
    async def pre_run_step(self, *, state: "State", action: "Action", **future_kwargs: Any):
        pass


@lifecycle.base_hook("post_run_step")
class PostRunStepHook(abc.ABC):
    @abc.abstractmethod
    def post_run_step(
        self,
        *,
        state: "State",
        action: "Action",
        result: Optional[dict],
        exception: Exception,
        **future_kwargs: Any,
    ):
        pass


@lifecycle.base_hook("post_run_step")
class PostRunStepHookAsync(abc.ABC):
    @abc.abstractmethod
    async def post_run_step(
        self,
        *,
        state: "State",
        action: "Action",
        result: Optional[dict],
        exception: Exception,
        **future_kwargs: Any,
    ):
        pass


# THESE ARE NOT IN USE
# TODO -- implement/decide how to use them
@lifecycle.base_hook("pre_run_application")
class PreRunApplicationHook(abc.ABC):
    @abc.abstractmethod
    def pre_run_application(self, *, state: "State", **future_kwargs: Any):
        pass


@lifecycle.base_hook("pre_run_application")
class PreRunApplicationHookAsync(abc.ABC):
    @abc.abstractmethod
    async def pre_run_application(self, *, state: "State", **future_kwargs):
        pass


@lifecycle.base_hook("post_run_application")
class PostRunApplicationHook(abc.ABC):
    @abc.abstractmethod
    def post_run_application(
        self, *, state: "State", until: list[str], results: list[dict], **future_kwargs
    ):
        pass


@lifecycle.base_hook("post_run_application")
class PostRunApplicationHookAsync(abc.ABC):
    @abc.abstractmethod
    async def post_run_application(
        self, *, state: "State", until: list[str], results: list[dict], **future_kwargs
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
]
