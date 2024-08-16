import asyncio
from contextvars import ContextVar
from typing import Any, Dict, Optional

from burr.lifecycle.base import (
    DoLogAttributeHook,
    PostEndSpanHook,
    PostEndSpanHookAsync,
    PreStartSpanHook,
    PreStartSpanHookAsync,
)
from burr.lifecycle.internal import LifecycleAdapterSet
from burr.visibility import tracing
from burr.visibility.tracing import ActionSpan, TracerFactory

# There are a lot of state-specific assertions in this file
# We try to comment them. We should also probably organize them to be
# smaller and test specific things, but this is easier to validate for now


def is_subset(dict_subset, dict_full):
    return all(item in dict_full.items() for item in dict_subset.items())


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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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
        app_id="test_app_id",
        partition_key=None,
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


class AttributeHook(DoLogAttributeHook):
    def do_log_attributes(
        self,
        *,
        attributes: Dict[str, Any],
        action: str,
        action_sequence_id: int,
        span: Optional["ActionSpan"],
        tags: dict,
        **future_kwargs: Any,
    ):
        self.attributes.append(
            (attributes, action, action_sequence_id, span.uid if span is not None else None)
        )

    def __init__(self):
        self.attributes = []


async def test_log_attributes_called(request):
    hook = AttributeHook()
    adapter_set = LifecycleAdapterSet(hook)
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(request.node.name, default=None)
    tracer_factory_0 = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
    )
    # 0:0
    tracer_factory_0.log_attributes(key="root:0")
    async with tracer_factory_0("0") as t:
        t.log_attributes(key="0:0")
        # 0:0.0
        async with tracer_factory_0("0.0") as t:
            t.log_attributes(key="0.0:0")
            t.log_attributes(key="0.0:1")
        # 0:0.1
        async with tracer_factory_0("0.1") as t:
            t.log_attributes(key="0:0.1")
    # 0:1
    async with tracer_factory_0("1") as t:
        t.log_attributes(key="1:0")
        t.log_attributes(key="1:1")
        # 0:1.0
        async with tracer_factory_0("1.0") as t:
            t.log_attributes(key="1.0:0")
            t.log_attributes(key="1.0:1")
            # 0:1.0.0
            async with tracer_factory_0("1.0.0") as t:
                t.log_attributes(key="1.0.0:0")
                t.log_attributes(key="1.0.0:1")
            # 0:1.0.1
            async with tracer_factory_0("1.0.1") as t:
                t.log_attributes(key="1.0.1:0")
                t.log_attributes(key="1.0.1:1")
    tracer_factory_1 = TracerFactory(
        action="test_action",
        sequence_id=tracer_factory_0.action_sequence_id + 1,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
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
    assert hook.attributes == [
        ({"key": "root:0"}, "test_action", 0, None),
        ({"key": "0:0"}, "test_action", 0, "0:0"),
        ({"key": "0.0:0"}, "test_action", 0, "0:0.0"),
        ({"key": "0.0:1"}, "test_action", 0, "0:0.0"),
        ({"key": "0:0.1"}, "test_action", 0, "0:0.1"),
        ({"key": "1:0"}, "test_action", 0, "0:1"),
        ({"key": "1:1"}, "test_action", 0, "0:1"),
        ({"key": "1.0:0"}, "test_action", 0, "0:1.0"),
        ({"key": "1.0:1"}, "test_action", 0, "0:1.0"),
        ({"key": "1.0.0:0"}, "test_action", 0, "0:1.0.0"),
        ({"key": "1.0.0:1"}, "test_action", 0, "0:1.0.0"),
        ({"key": "1.0.1:0"}, "test_action", 0, "0:1.0.1"),
        ({"key": "1.0.1:1"}, "test_action", 0, "0:1.0.1"),
    ]


def test_trace_decorator_single_fn(request):
    # Mock an action span context var
    # This is set by the tracer factory, which uses the default in tracing
    # This is so we know the current (context aware) span
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    # Mock a tracer factory context var
    # This is set usually by the application so the decorator knows what to get
    tracer_factory_context_var = ContextVar[TracerFactory](
        request.node.name + "_tracer", default=None
    )
    # Create a hook so we can wire it through and ensure the right thing gets called
    hook = AttributeHook()
    adapter_set = LifecycleAdapterSet(hook)

    # Create and set the var to a tracer factory that is context-aware
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
    )
    tracer_factory_context_var.set(tracer_factory)
    # Nothing set now
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans
    # Instantiate a decorator that will set the action span when it enters, and unset once it leaves
    decorator = tracing.trace(
        _context_var=tracer_factory_context_var, input_filterlist=["filtered_out"]
    )

    # Then the function can assert things for us
    # We ensure it gets called by checking the output
    def foo(a: int, b: int, filtered_out: str = "not_present") -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == foo.__name__  # span name should match the function name
        assert action_span_context.child_count == 0  # no children (now)
        return a + b

    decorated_foo = decorator(foo)
    result = decorated_foo(1, 2)
    assert result == 3
    assert is_subset({"a": 1, "b": 2}, hook.attributes[0][0])
    assert is_subset({"return": 3}, hook.attributes[2][0])


async def test_trace_decorator_single_fn_async(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    tracer_factory_context_var = ContextVar[TracerFactory](
        request.node.name + "_tracer", default=None
    )
    hook = AttributeHook()
    adapter_set = LifecycleAdapterSet(hook)

    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=adapter_set,
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
    )
    tracer_factory_context_var.set(tracer_factory)
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans
    decorator = tracing.trace(
        _context_var=tracer_factory_context_var, input_filterlist=["filtered_out"]
    )

    async def foo(a: int, b: int, filtered_out: str = "not_present") -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == foo.__name__  # span name should match the function name
        assert action_span_context.child_count == 0  # no children (now)
        await asyncio.sleep(0.001)
        return a + b

    decorated_foo = decorator(foo)
    result = await decorated_foo(1, 2)
    assert result == 3
    assert is_subset({"a": 1, "b": 2}, hook.attributes[0][0])
    assert is_subset({"return": 3}, hook.attributes[2][0])


def test_trace_decorator_recursive(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    hook = AttributeHook()
    tracer_factory_context_var = ContextVar[TracerFactory](
        request.node.name + "_tracer", default=None
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(hook),
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
    )
    tracer_factory_context_var.set(tracer_factory)
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans
    decorator = tracing.trace(_context_var=tracer_factory_context_var)

    @decorator
    def foo(a: int, b: int) -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == foo.__name__  # span name should match the function name
        return bar(a + 1, a + b) + a + b

    @decorator
    def bar(a: int, b: int) -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == bar.__name__  # span name should match the function name
        assert action_span_context.child_count == 0  # no children (now)
        assert action_span_context.parent.name == foo.__name__  # parent should be foo
        return a * b

    result = foo(1, 2)
    assert result == 9
    assert is_subset({"a": 1, "b": 2}, hook.attributes[0][0])
    assert is_subset({"a": 2, "b": 3}, hook.attributes[2][0])
    assert is_subset({"return": 6}, hook.attributes[4][0])
    assert is_subset({"return": 9}, hook.attributes[5][0])


async def test_trace_decorator_recursive_async(request):
    context_var: ContextVar[Optional[ActionSpan]] = ContextVar(
        request.node.name,
        default=None,
    )
    hook = AttributeHook()
    tracer_factory_context_var = ContextVar[TracerFactory](
        request.node.name + "_tracer", default=None
    )
    tracer_factory = TracerFactory(
        action="test_action",
        sequence_id=0,
        lifecycle_adapters=LifecycleAdapterSet(hook),
        _context_var=context_var,
        app_id="test_app_id",
        partition_key=None,
    )
    tracer_factory_context_var.set(tracer_factory)
    assert context_var.get() is None  # nothing to start
    assert tracer_factory.top_level_span_count == 0  # and thus no top-level spans
    decorator = tracing.trace(_context_var=tracer_factory_context_var)

    @decorator
    async def foo(a: int, b: int) -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == foo.__name__  # span name should match the function name
        await asyncio.sleep(0.001)
        return await bar(a + 1, a + b) + a + b

    @decorator
    async def bar(a: int, b: int) -> int:
        action_span_context = context_var.get()
        assert action_span_context is not None  # context is now set as we entered the manager
        assert action_span_context.name == bar.__name__  # span name should match the function name
        assert action_span_context.child_count == 0  # no children (now)
        assert action_span_context.parent.name == foo.__name__  # parent should be foo
        await asyncio.sleep(0.001)
        return a * b

    result = await foo(1, 2)
    assert result == 9
    assert is_subset({"a": 1, "b": 2}, hook.attributes[0][0])
    assert is_subset({"a": 2, "b": 3}, hook.attributes[2][0])
    assert is_subset({"return": 6}, hook.attributes[4][0])
    assert is_subset({"return": 9}, hook.attributes[5][0])
