import dataclasses
import json
import logging
import random
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Sequence, Tuple

from burr.integrations.base import require_plugin

logger = logging.getLogger(__name__)

try:
    from opentelemetry import context
    from opentelemetry import context as context_api
    from opentelemetry import trace
    from opentelemetry.sdk.trace import Span, SpanProcessor, TracerProvider
    from opentelemetry.trace import get_current_span, use_span
except ImportError as e:
    require_plugin(
        e,
        "opentelemetry",
    )

from burr.common import types as burr_types
from burr.core import Action, ApplicationGraph, State, serde
from burr.lifecycle import (
    PostApplicationExecuteCallHook,
    PostRunStepHook,
    PreApplicationExecuteCallHook,
    PreRunStepHook,
)
from burr.lifecycle.base import DoLogAttributeHook, ExecuteMethod, PostEndSpanHook, PreStartSpanHook
from burr.tracking import LocalTrackingClient
from burr.tracking.base import SyncTrackingClient
from burr.visibility import ActionSpan

# We have to keep track of tokens for the span
# As OpenTel has some weird behavior around context managers, we have to account for the latest ones we started
# This way we can pop one off and know where to set the current one (as the parent, when the next one ends)
token_stack = ContextVar[Optional[List[Tuple[object, Span]]]]("token_stack", default=None)


@dataclasses.dataclass
class FullSpanContext:
    action_span: ActionSpan
    partition_key: str
    app_id: str


span_map = {}


def cache_span(span: Span, context: FullSpanContext) -> Span:
    span_map[span.get_span_context().span_id] = context
    return span


def uncache_span(span: Span) -> Span:
    del span_map[span.get_span_context().span_id]
    return span


def get_cached_span(span_id: int) -> Optional[FullSpanContext]:
    return span_map.get(span_id)


tracker_context = ContextVar[Optional[SyncTrackingClient]]("tracker_context", default=None)


def _is_homogeneous_sequence(value: Sequence):
    if len(value) == 0:
        return True
    first_type = type(value[0])
    return all([isinstance(val, first_type) for val in value])


def convert_to_otel_attribute(attr: Any):
    if isinstance(attr, (str, bool, float, int)):
        return attr
    elif isinstance(attr, Sequence):
        if _is_homogeneous_sequence(attr):
            return list(attr)
    try:
        return json.dumps(serde.serialize(attr))
    except Exception as e:
        logger.error(f"Failed to serialize attribute: {attr}, got error: {e}")
        return str(attr)


def _exit_span(exc: Optional[Exception] = None):
    """Ditto with _enter_span, but for exiting the span. Pops the token off the stack and detaches the context."""
    stack = token_stack.get()[:]
    token, span = stack.pop()
    token_stack.set(stack)
    context.detach(token)
    if exc:
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
    else:
        span.set_status(trace.Status(trace.StatusCode.OK))
    span.end()
    return span


def _enter_span(name: str, tracer: trace.Tracer):
    """Utility function to enter a span. Starts, sets the current context, and adds it to the token stack.

    See this for some background on why start_span doesn't really work. We could use start_as_current_span,
    but this is a bit more explicit.
    """
    span = tracer.start_span(
        name=name,
        record_exception=False,  # we'll handle this ourselves
        set_status_on_exception=False,
    )
    ctx = trace.set_span_in_context(span)
    token = context.attach(ctx)
    stack = (token_stack.get() or [])[:]
    stack.append((token, span))
    token_stack.set(stack)
    return span


class OpenTelemetryBridge(
    PreApplicationExecuteCallHook,
    PostApplicationExecuteCallHook,
    PreRunStepHook,
    PostRunStepHook,
    PreStartSpanHook,
    PostEndSpanHook,
    DoLogAttributeHook,
):
    """Adapter to log Burr events to OpenTelemetry. At a high level, this works as follows:
    1. On any of the start/pre hooks (pre_run_execute_call, pre_run_step, pre_start_span), we start a new span
    2. On any of the post ones we exit the span, accounting for the error (setting it if needed)
    3. On do_log_attributes, we log the attributes to the current span -- these are serialized using the serde module

    This works by logging to OpenTelemetry, and setting the span processor to be the right one (that knows about the tracker).
    """

    def __init__(self, tracer_name: str = None, tracer: trace.Tracer = None):
        """Initializes an OpenTel adapter. Passes in a tracer_name or a tracer object,
        should only pass one.

        :param tracer_name: Name of the tracer if you want it to initialize for you -- not including it will use a default
        :param tracer: Tracer object if you want to pass it in yourself
        """
        if tracer_name and tracer:
            raise ValueError(
                f"Only pass in one of tracer_name or tracer, not both, got: tracer_name={tracer_name} and tracer={tracer}"
            )
        if tracer:
            self.tracer = tracer
        else:
            self.tracer = trace.get_tracer(__name__ if tracer_name is None else tracer_name)

    def pre_run_execute_call(
        self,
        *,
        method: ExecuteMethod,
        **future_kwargs: Any,
    ):
        # TODO -- handle links -- we need to wire this through
        _enter_span(method.value, self.tracer)

    def do_log_attributes(
        self,
        *,
        attributes: Dict[str, Any],
        **future_kwargs: Any,
    ):
        otel_span = get_current_span()
        if otel_span is None:
            logger.warning(
                "Attempted to log attributes from the tracker outside of a span, ignoring"
            )
            return
        otel_span.set_attributes(
            {key: convert_to_otel_attribute(value) for key, value in attributes.items()}
        )

    def pre_run_step(
        self,
        *,
        action: "Action",
        **future_kwargs: Any,
    ):
        _enter_span(action.name, self.tracer)

    def pre_start_span(
        self,
        *,
        span: "ActionSpan",
        **future_kwargs: Any,
    ):
        _enter_span(span.name, self.tracer)

    def post_end_span(
        self,
        *,
        span: "ActionSpan",
        **future_kwargs: Any,
    ):
        # TODO -- wire through exceptions
        _exit_span()

    def post_run_step(
        self,
        *,
        exception: Exception,
        **future_kwargs: Any,
    ):
        _exit_span(exception)

    def post_run_execute_call(
        self,
        *,
        exception: Optional[Exception],
        **future_kwargs,
    ):
        _exit_span(exception)


class OpenTelemetryTracker(
    SyncTrackingClient,
):
    """Tracker that includes logging of OpenTelemetry events. Note you will be unlikely to instantiate this directly,
    rather, you will instantiate it through with_tracker(use_oteL_tracing=True) on the ApplicationBuilder.

    At a high level, this:
    1. Logs all events to OpenTelemetry
    2. Adds a span processor to opentelemetry

    Note that this globally sets a tracer provider -- it is possible that this will interfere with
    other tracers, and we are actively investigating it.
    """

    def __init__(self, burr_tracker: SyncTrackingClient):
        initialize_tracer()
        self.tracer = trace.get_tracer("burr.integrations.opentelemetry")
        self.burr_tracker = burr_tracker

    def post_application_create(
        self,
        *,
        app_id: str,
        partition_key: Optional[str],
        state: "State",
        application_graph: "ApplicationGraph",
        parent_pointer: Optional[burr_types.ParentPointer],
        spawning_parent_pointer: Optional[burr_types.ParentPointer],
        **future_kwargs: Any,
    ):
        self.burr_tracker.post_application_create(
            app_id=app_id,
            partition_key=partition_key,
            state=state,
            application_graph=application_graph,
            parent_pointer=parent_pointer,
            spawning_parent_pointer=spawning_parent_pointer,
        )

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
        # TODO -- get current span then call attributes
        # We need to serialize as well, attributes are not the right type to match 100%
        otel_span = get_current_span()
        if otel_span is None:
            # TODO -- see if this shows up then make it a les aggressive error
            raise ValueError("No current span")
        otel_span.set_attributes(
            {key: convert_to_otel_attribute(value) for key, value in attributes.items()}
        )

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
        self.burr_tracker.pre_run_step(
            app_id=app_id,
            partition_key=partition_key,
            sequence_id=sequence_id,
            state=state,
            action=action,
            inputs=inputs,
            **future_kwargs,
        )
        tracker_context.set(self.burr_tracker)
        span = _enter_span(action.name, self.tracer)
        cache_span(
            span,
            FullSpanContext(
                action_span=ActionSpan.create_initial(
                    action=action.name,
                    name=action.name,
                    sequence_id=0,
                    action_sequence_id=sequence_id,
                ),
                partition_key=partition_key,
                app_id=app_id,
            ),
        )

    def pre_start_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        otel_span = _enter_span(span.name, self.tracer)
        return otel_span

    def post_end_span(
        self,
        *,
        action: str,
        action_sequence_id: int,
        span: "ActionSpan",
        span_dependencies: list[str],
        app_id: str,
        partition_key: Optional[str],
        **future_kwargs: Any,
    ):
        # TODO -- wire through exceptions
        _exit_span()

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
        self.burr_tracker.post_run_step(
            app_id=app_id,
            partition_key=partition_key,
            sequence_id=sequence_id,
            state=state,
            action=action,
            result=result,
            exception=exception,
        )
        _exit_span(exception)
        tracker_context.set(None)


class BurrTrackingSpanProcessor(SpanProcessor):
    @property
    def tracker(self):
        """Quick trick to get closer to the right tracker. This is suboptimal as we don't really
        have guarentees that we'll be *in* the right context when it gets logged, but the way OpenTel
        is implemented we will (with the immediate span processor). TODO -- track a map of span ID -> tracker
        """
        return tracker_context.get()

    def on_start(
        self,
        span: "Span",
        parent_context: Optional[context_api.Context] = None,
    ) -> None:
        # First get the ID of the parent so we can retrieve from our cache
        parent_id = span.parent.span_id if span.parent is not None else None
        if parent_id is not None:
            parent_span = get_cached_span(span.parent.span_id)
            # If it exists, we can spawn a new span and cache that
            if parent_span is not None:
                cache_span(
                    span,
                    context := FullSpanContext(
                        action_span=parent_span.action_span.spawn(span.name),
                        partition_key=parent_span.partition_key,
                        app_id=parent_span.app_id,
                    ),
                )
                self.tracker.pre_start_span(
                    action=context.action_span.action,
                    action_sequence_id=context.action_span.action_sequence_id,
                    span=context.action_span,
                    span_dependencies=[],  # TODO -- log
                    app_id=context.app_id,
                    partition_key=context.partition_key,
                )

    def on_end(self, span: "Span") -> None:
        cached_span = get_cached_span(span.get_span_context().span_id)
        # If this is none it means we're outside of the burr context
        if cached_span is not None:
            # TODO -- get tracker context to work
            self.tracker.post_end_span(
                action=cached_span.action_span.action,
                action_sequence_id=cached_span.action_span.action_sequence_id,
                span=cached_span.action_span,
                span_dependencies=[],  # TODO -- log
                app_id=cached_span.app_id,
                partition_key=cached_span.partition_key,
            )
            uncache_span(span)
            if len(span.attributes) > 0:
                self.tracker.do_log_attributes(
                    attributes=dict(**span.attributes),
                    action=cached_span.action_span.action,
                    action_sequence_id=cached_span.action_span.action_sequence_id,
                    span=cached_span.action_span,
                    tags={},  # TODO -- log
                    app_id=cached_span.app_id,
                    partition_key=cached_span.partition_key,
                )


initialized = False


def initialize_tracer():
    """Initializes the tracer for OpenTel. Note this sets it globally.
    TODO -- ensure that it is initialized properly/do this in a cleaner manner.
    OpenTel does not make this easy as it's all global state.
    """
    global initialized
    if initialized:
        return
    initialized = True
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(BurrTrackingSpanProcessor())


if __name__ == "__main__":
    initialize_tracer()
    tracer = trace.get_tracer(__name__)
    tracker = LocalTrackingClient("otel_test")
    opentel_adapter = OpenTelemetryTracker(burr_tracker=tracker)

    import time

    from burr.core import ApplicationBuilder, Result, action, default, expr
    from burr.visibility import TracerFactory

    def slp():
        time.sleep(random.random())

    @action(reads=["count"], writes=["count"])
    def counter(state: State, __tracer: TracerFactory) -> State:
        with __tracer("foo"):
            slp()
            with __tracer("bar"):
                slp()
                with tracer.start_span("baz") as span:
                    with use_span(span, end_on_exit=True):
                        slp()
                    with tracer.start_as_current_span("qux"):
                        slp()
                    with tracer.start_as_current_span("quux"):
                        slp()
                    slp()

                slp()
        return state.update(count=state["count"] + 1)

    result_action = Result("count").with_name("result")
    app = (
        ApplicationBuilder()
        .with_actions(result_action, counter=counter)
        .with_transitions(("counter", "counter", expr("count<10")))
        .with_transitions(("counter", "result", default))
        .with_hooks(opentel_adapter)
        .with_entrypoint("counter")
        # .with_tracker(tracker)
        .with_state(count=0)
        .build()
    )
    app.run(halt_after=["result"])
