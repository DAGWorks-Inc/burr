import json
import os
import uuid
from typing import Literal, Optional, Tuple

import pytest

import burr
from burr.core import Application, ApplicationBuilder, Result, State, action, default, expr
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
