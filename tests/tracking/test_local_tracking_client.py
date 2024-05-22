import json
import os
import uuid
from typing import Literal, Optional, Tuple

import pytest

import burr
from burr import lifecycle
from burr.core import Action, Application, ApplicationBuilder, Result, State, action, default, expr
from burr.core.persistence import BaseStatePersister, PersistedStateData
from burr.tracking import LocalTrackingClient
from burr.tracking.client import _allowed_project_name
from burr.tracking.common.models import (
    ApplicationMetadataModel,
    ApplicationModel,
    BeginEntryModel,
    BeginSpanModel,
    EndEntryModel,
    EndSpanModel,
)
from burr.visibility import TracerFactory


@action(reads=["counter", "break_at"], writes=["counter"])
def counter(state: State, __tracer: TracerFactory) -> Tuple[dict, State]:
    with __tracer("increment"):
        result = {"counter": state["counter"] + 1}
    if state["break_at"] == result["counter"]:
        raise ValueError("Broken")
    return result, state.update(**result)


def sample_application(project_name: str, log_dir: str, app_id: str, broken: bool = False):
    return (
        burr.core.ApplicationBuilder()
        .with_state(counter=0, break_at=2 if broken else -1)
        .with_actions(counter=counter, result=Result("counter"))
        .with_transitions(
            ("counter", "counter", expr("counter < 2")),  # just count to two for testing
            ("counter", "result", default),
        )
        .with_entrypoint("counter")
        .with_tracker(project=project_name, tracker="local", params={"storage_dir": log_dir})
        .with_identifiers(app_id=app_id)
        .build()
    )


def test_application_tracks_end_to_end(tmpdir: str):
    app_id = str(uuid.uuid4())
    log_dir = os.path.join(tmpdir, "tracking")
    project_name = "test_application_tracks_end_to_end"
    app = sample_application(project_name, log_dir, app_id)
    app.run(halt_after=["result"])
    results_dir = os.path.join(log_dir, project_name, app_id)
    assert os.path.exists(results_dir)
    assert os.path.exists(log_output := os.path.join(results_dir, LocalTrackingClient.LOG_FILENAME))
    assert os.path.exists(
        graph_output := os.path.join(results_dir, LocalTrackingClient.GRAPH_FILENAME)
    )
    with open(log_output) as f:
        log_contents = [json.loads(item) for item in f.readlines()]
    with open(graph_output) as f:
        graph_contents = json.load(f)
    assert graph_contents["type"] == "application"
    app_model = ApplicationModel.parse_obj(graph_contents)
    assert app_model.entrypoint == "counter"
    assert app_model.actions[0].name == "counter"
    assert app_model.actions[1].name == "result"
    pre_run = [
        BeginEntryModel.model_validate(line)
        for line in log_contents
        if line["type"] == "begin_entry"
    ]
    post_run = [
        EndEntryModel.model_validate(line) for line in log_contents if line["type"] == "end_entry"
    ]
    span_start_model = [
        BeginSpanModel.model_validate(line) for line in log_contents if line["type"] == "begin_span"
    ]
    span_end_model = [
        EndSpanModel.model_validate(line) for line in log_contents if line["type"] == "end_span"
    ]
    assert len(pre_run) == 3
    assert len(post_run) == 3
    assert len(span_start_model) == 2  # two custom-defined spans
    assert len(span_end_model) == 2  # ditto
    assert not any(item.exception for item in post_run)


def test_application_tracks_end_to_end_broken(tmpdir: str):
    app_id = str(uuid.uuid4())
    log_dir = os.path.join(tmpdir, "tracking")
    project_name = "test_application_tracks_end_to_end"
    app = sample_application(project_name, log_dir, app_id, broken=True)
    with pytest.raises(ValueError):
        app.run(halt_after=["result"])
    results_dir = os.path.join(log_dir, project_name, app_id)
    assert os.path.exists(results_dir)
    assert os.path.exists(log_output := os.path.join(results_dir, LocalTrackingClient.LOG_FILENAME))
    assert os.path.exists(
        graph_output := os.path.join(results_dir, LocalTrackingClient.GRAPH_FILENAME)
    )
    with open(log_output) as f:
        log_contents = [json.loads(item) for item in f.readlines()]
    with open(graph_output) as f:
        graph_contents = json.load(f)
    assert graph_contents["type"] == "application"
    app_model = ApplicationModel.model_validate(graph_contents)
    assert app_model.entrypoint == "counter"
    assert app_model.actions[0].name == "counter"
    assert app_model.actions[1].name == "result"
    pre_run = [
        BeginEntryModel.model_validate(line)
        for line in log_contents
        if line["type"] == "begin_entry"
    ]
    post_run = [
        EndEntryModel.model_validate(line) for line in log_contents if line["type"] == "end_entry"
    ]
    assert len(pre_run) == 2
    assert len(post_run) == 2
    assert len(post_run[-1].exception) > 0 and "Broken" in post_run[-1].exception


@pytest.mark.parametrize(
    "input_string, on_windows, expected_result",
    [
        ("Hello-World_123", False, True),
        ("Hello:World_123", False, True),
        ("Hello:World_123", True, False),
        ("Invalid:Chars*", False, False),
        ("Just$ymbols", True, False),
        ("Normal_Text", True, True),
    ],
)
def test__allowed_project_name(input_string, on_windows, expected_result):
    assert _allowed_project_name(input_string, on_windows) == expected_result


class DummyPersister(BaseStatePersister):
    """Dummy persistor."""

    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None, **kwargs
    ) -> Optional[PersistedStateData]:
        return PersistedStateData(
            partition_key="user123",
            app_id="123",
            sequence_id=5,
            position="counter",
            state=State({"count": 5}),
            created_at="",
            status="completed",
        )

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        return ["123"]

    def save(
        self,
        partition_key: Optional[str],
        app_id: str,
        sequence_id: int,
        position: str,
        state: State,
        status: Literal["completed", "failed"],
        **kwargs,
    ):
        return


def test_persister_tracks_parent(tmpdir):
    result = Result("count").with_name("result")
    old_app_id = "old"
    new_app_id = "new"
    log_dir = os.path.join(tmpdir, "tracking")
    results_dir = os.path.join(log_dir, "test_persister_tracks_parent", new_app_id)
    project_name = "test_persister_tracks_parent"
    app: Application = (
        ApplicationBuilder()
        .with_actions(counter, result)
        .with_transitions(("counter", "result", default))
        .initialize_from(
            DummyPersister(),
            resume_at_next_action=True,
            default_state={},
            default_entrypoint="counter",
            fork_from_app_id=old_app_id,
            fork_from_partition_key="user123",
            fork_from_sequence_id=5,
        )
        .with_identifiers(app_id=new_app_id, partition_key="user123")
        .with_tracker(project=project_name, tracker="local", params={"storage_dir": log_dir})
        .build()
    )
    app.run(halt_after=["result"])
    assert os.path.exists(
        graph_output := os.path.join(results_dir, LocalTrackingClient.METADATA_FILENAME)
    )
    with open(graph_output) as f:
        metadata = json.load(f)
    metadata_parsed = ApplicationMetadataModel.model_validate(metadata)
    assert metadata_parsed.partition_key == "user123"
    assert metadata_parsed.parent_pointer.app_id == old_app_id
    assert metadata_parsed.parent_pointer.sequence_id == 5
    assert metadata_parsed.parent_pointer.partition_key == "user123"


def test_multi_fork_tracking_client(tmpdir):
    """This is more of an end-to-end test. We shoudl probably break it out
    into smaller tests but the local tracking client being used as a persister is
    a bit of a complex case, and we don't want to get lost in the details.
    """
    common_app_id = uuid.uuid4()
    initial_app_id = f"new_{common_app_id}"
    # newer_app_id = "newer"
    log_dir = os.path.join(tmpdir, "tracking")
    # results_dir = os.path.join(log_dir, "test_persister_tracks_parent", new_app_id)
    project_name = "test_persister_tracks_parent"

    tracking_client = LocalTrackingClient(project=project_name, storage_dir=log_dir)

    class CallTracker(lifecycle.PostRunStepHook):
        def __init__(self):
            self.count = 0

        def post_run_step(self, action: Action, **kwargs):
            if action.name == "counter":
                self.count += 1

    def create_application(
        old_app_id: Optional[str], new_app_id: str, old_sequence_id: Optional[int], max_count: int
    ) -> Tuple[Application, CallTracker]:
        tracker = CallTracker()
        app: Application = (
            ApplicationBuilder()
            .with_actions(counter, Result("count").with_name("result"))
            .with_transitions(
                ("counter", "counter", expr(f"counter < {max_count}")),
                ("counter", "result", default),
            )
            .initialize_from(
                tracking_client,
                resume_at_next_action=True,
                default_state={"counter": 0, "break_at": -1},  # never break
                default_entrypoint="counter",
                fork_from_app_id=old_app_id,
                fork_from_sequence_id=old_sequence_id,
            )
            .with_identifiers(app_id=new_app_id)
            .with_tracker(tracking_client)
            .with_hooks(tracker)
            .build()
        )
        return app, tracker

    # create an initial one
    app_initial, tracker = create_application(None, initial_app_id, None, max_count=10)
    action_, result, state = app_initial.run(halt_after=["result"])  # Run all the way through
    assert state["counter"] == 10  # should have counted to 10
    assert tracker.count == 10  # 10 counts

    # create a new one from position 5

    forked_app_id = f"fork_1_{common_app_id}"
    forked_app_1, tracker = create_application(initial_app_id, forked_app_id, 5, max_count=15)
    assert forked_app_1.sequence_id == 5
    action_, result, state = forked_app_1.run(halt_after=["result"])  # Run all the way through
    assert state["counter"] == 15  # should have counted to 15
    assert tracker.count == 9  # start at 6, go to 15
    assert forked_app_1.parent_pointer.app_id == initial_app_id
    assert forked_app_1.parent_pointer.sequence_id == 5

    forked_forked_app_id = f"fork_2_{common_app_id}"
    forked_app_2, tracker = create_application(
        forked_app_id, forked_forked_app_id, 10, max_count=25
    )
    assert forked_app_2.sequence_id == 10
    action_, result, state = forked_app_2.run(halt_after=["result"])  # Run all the way through
    assert state["counter"] == 25  # should have counted to 15
    assert tracker.count == 14  # start at 11, go to 20

    assert forked_app_2.parent_pointer.app_id == forked_app_id
    assert forked_app_2.parent_pointer.sequence_id == 10
