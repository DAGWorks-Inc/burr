import asyncio
from contextvars import ContextVar
from typing import Any, Optional

from burr.lifecycle.base import (
    PostEndSpanHook,
    PostEndSpanHookAsync,
    PreStartSpanHook,
    PreStartSpanHookAsync,
)
from burr.lifecycle.internal import LifecycleAdapterSet
from burr.visibility.tracing import ActionSpan, TracerFactory

# There are a lot of state-specific assertions in this file
# We try to comment them. We should also probably organize them to be
# smaller and test specific things, but this is easier to validate for now


def test_action_span_tracer_correct_span_count(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(),
        _context_var=context_var,
    )
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans

    with tracer_factory("0") as span_0:
        assert span_0.span_name == "0"  # span name should match the factory call
        context = context_var.get()
        assert context is not None  # context is now set as we entered the manager
        assert context.child_count == 0  # no children yet
        assert context.action == "test_action"  # action name should match the factory
        assert context.parent is None  # one of the top-level/roots
        assert context.sequence_id == 0  # first one

    context = context_var.get()
    assert context is None  # context is now unset
    assert tracer_factory.top_level_span_count == 1  # we have one now


async def test_action_span_tracer_correct_span_count_async(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(),
        _context_var=context_var,
    )
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans

    async with tracer_factory("0") as span_0:
        assert span_0.span_name == "0"  # span name should match the factory call
        context = context_var.get()
        assert context is not None  # context is now set as we entered the manager
        assert context.child_count == 0  # no children yet
        assert context.action == "test_action"  # action name should match the factory
        assert context.parent is None  # one of the top-level/roots
        assert context.sequence_id == 0  # first one

    context = context_var.get()
    assert context is None  # context is now unset
    assert tracer_factory.top_level_span_count == 1  # we have one now


def test_action_span_tracer_correct_span_count_nested(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(),
        _context_var=context_var,
    )

    with tracer_factory("0") as outside_span_0:
        with tracer_factory("0.0"):
            context = context_var.get()
            assert context.child_count == 0  # no children
            assert context.parent.name == outside_span_0.span_name  # one of the top-level/roots
            assert context.sequence_id == 0  # first one

        with tracer_factory("0.1"):
            context = context_var.get()
            assert context.sequence_id == 1  # this is the second one

        assert outside_span_0.top_level_span_count == 1  # we only have one top-level span

        context = context_var.get()
        assert context.child_count == 2  # two children we spawned above
        assert context.name == outside_span_0.span_name  # we're back to the outside span

    with tracer_factory("1") as outside_span_1:
        assert outside_span_1.top_level_span_count == 2  # now we have another
    assert tracer_factory.top_level_span_count == 2  # the tracer factory holds state

    context = context_var.get()
    assert context is None  # context gets reset at the end


async def test_action_span_tracer_correct_span_count_nested_async(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(),
        _context_var=context_var,
    )

    async with tracer_factory("0") as outside_span_0:
        async with tracer_factory("0.0"):
            context = context_var.get()
            assert context.child_count == 0  # no children
            assert context.parent.name == outside_span_0.span_name  # one of the top-level/roots
            assert context.sequence_id == 0  # first one

        async with tracer_factory("0.1"):
            context = context_var.get()
            assert context.sequence_id == 1  # this is the second one

        assert outside_span_0.top_level_span_count == 1  # we only have one top-level span

        context = context_var.get()
        assert context.child_count == 2  # two children we spawned above
        assert context.name == outside_span_0.span_name  # we're back to the outside span

    async with tracer_factory("1") as outside_span_1:
        assert outside_span_1.top_level_span_count == 2  # now we have another
    assert tracer_factory.top_level_span_count == 2  # the tracer factory holds state

    context = context_var.get()
    assert context is None  # context gets reset at the end


def test_action_span_spawn():
    action_span = ActionSpan.create_initial("test_action", "0", 0, action_sequence_id=0)
    assert action_span.parent is None  # this is the top-level span
    spawned_0 = action_span.spawn("0.0")
    assert spawned_0.sequence_id == 0
    assert spawned_0.parent is action_span  # this is a child of the top-level span
    spawned_1 = action_span.spawn("0.1")  # another child
    assert spawned_1.sequence_id == 1
    assert action_span.child_count == 2
    assert action_span.sequence_id == 0


def test_pre_span_lifecycle_hooks_called(request):
    class TrackingHook(PreStartSpanHook, PostEndSpanHook):
        def __init__(self):
            self.uids_pre = []
            self.uids_post = []

        def pre_start_span(
            self,
            *,
            span: "ActionSpan",
            **future_kwargs: Any,
        ):
            self.uids_pre.append(span.uid)

        def post_end_span(
            self,
            *,
            span: "ActionSpan",
            **future_kwargs: Any,
        ):
            self.uids_post.append(span.uid)

    hook = TrackingHook()
    adapter_set = LifecycleAdapterSet(hook)
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(request.node.name, default=None)
    tracer_factory_0 = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
    )
    # 0:0
    with tracer_factory_0("0"):
        # 0:0.0
        with tracer_factory_0("0.0"):
            pass
        # 0:0.1
        with tracer_factory_0("0.1"):
            pass
    # 0:1
    with tracer_factory_0("1"):
        # 0:1.0
        with tracer_factory_0("1.0"):
            # 0:1.0.0
            with tracer_factory_0("1.0.0"):
                pass
            # 0:1.0.1
            with tracer_factory_0("1.0.1"):
                pass
    tracer_factory_1 = TracerFactory(
        action="test_action",
        sequence_id=tracer_factory_0.action_sequence_id + 1,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
    )
    # 1:0
    with tracer_factory_1("2"):
        # 1:0.0
        with tracer_factory_1("2.0"):
            pass
        # 1:0.1
        with tracer_factory_1("2.1"):
            pass

    # order of this is exactly as expected -- in order traversal
    assert hook.uids_pre == [
        "0:0",
        "0:0.0",
        "0:0.1",
        "0:1",
        "0:1.0",
        "0:1.0.0",
        "0:1.0.1",
        "1:0",
        "1:0.0",
        "1:0.1",
    ]

    # order of this is a little trickier -- the containing span closes at the end so its post-order traversal
    assert hook.uids_post == [
        "0:0.0",
        "0:0.1",
        "0:0",
        "0:1.0.0",
        "0:1.0.1",
        "0:1.0",
        "0:1",
        "1:0.0",
        "1:0.1",
        "1:0",
    ]


async def test_pre_span_lifecycle_hooks_called_async(request):
    class AsyncTrackingHook(PreStartSpanHookAsync, PostEndSpanHookAsync):
        def __init__(self):
            self.uids_pre = []
            self.uids_post = []

        async def pre_start_span(
            self,
            *,
            span: "ActionSpan",
            **future_kwargs: Any,
        ):
            await asyncio.sleep(0.01)
            self.uids_pre.append(span.uid)

        async def post_end_span(
            self,
            *,
            span: "ActionSpan",
            **future_kwargs: Any,
        ):
            await asyncio.sleep(0.01)
            self.uids_post.append(span.uid)

    hook = AsyncTrackingHook()
    adapter_set = LifecycleAdapterSet(hook)
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(request.node.name, default=None)
    tracer_factory_0 = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
    )
    # 0:0
    async with tracer_factory_0("0"):
        # 0:0.0
        async with tracer_factory_0("0.0"):
            pass
        # 0:0.1
        async with tracer_factory_0("0.1"):
            pass
    # 0:1
    async with tracer_factory_0("1"):
        # 0:1.0
        async with tracer_factory_0("1.0"):
            # 0:1.0.0
            async with tracer_factory_0("1.0.0"):
                pass
            # 0:1.0.1
            async with tracer_factory_0("1.0.1"):
                pass
    tracer_factory_1 = TracerFactory(
        action="test_action",
        sequence_id=tracer_factory_0.action_sequence_id + 1,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
    )
    # 1:0
    async with tracer_factory_1("2"):
        # 1:0.0
        async with tracer_factory_1("2.0"):
            pass
        # 1:0.1
        async with tracer_factory_1("2.1"):
            pass

    # order of this is exactly as expected -- in order traversal
    assert hook.uids_pre == [
        "0:0",
        "0:0.0",
        "0:0.1",
        "0:1",
        "0:1.0",
        "0:1.0.0",
        "0:1.0.1",
        "1:0",
        "1:0.0",
        "1:0.1",
    ]

    # order of this is a little trickier -- the containing span closes at the end so its post-order traversal
    assert hook.uids_post == [
        "0:0.0",
        "0:0.1",
        "0:0",
        "0:1.0.0",
        "0:1.0.1",
        "0:1.0",
        "0:1",
        "1:0.0",
        "1:0.1",
        "1:0",
    ]
