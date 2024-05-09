import datetime
import json
import logging
import os
import re
import traceback
from typing import Any, Dict, Optional

from burr import system
from burr.core import Action, ApplicationGraph, State
from burr.core.persistence import BaseStateLoader, PersistedStateData
from burr.integrations.base import require_plugin
from burr.lifecycle import (
    PostApplicationCreateHook,
    PostEndSpanHook,
    PostRunStepHook,
    PreRunStepHook,
    PreStartSpanHook,
)
from burr.tracking.common.models import (
    ApplicationMetadataModel,
    ApplicationModel,
    BeginEntryModel,
    BeginSpanModel,
    EndEntryModel,
    EndSpanModel,
)
from burr.visibility import ActionSpan

logger = logging.getLogger(__name__)

try:
    import pydantic
except ImportError as e:
    require_plugin(
        e,
        ["pydantic"],
        "tracking-client",
    )


def _format_exception(exception: Exception) -> Optional[str]:
    if exception is None:
        return None
    return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))


def _allowed_project_name(project_name: str, on_windows: bool) -> bool:
    allowed_chars = "a-zA-Z0-9_\-"
    if not on_windows:
        allowed_chars += ":"
    pattern = f"^[{allowed_chars}]+$"

    # Use regular expression to check if the string is valid
    return bool(re.match(pattern, project_name))


class LocalTrackingClient(
    PostApplicationCreateHook,
    PreRunStepHook,
    PostRunStepHook,
    PreStartSpanHook,
    PostEndSpanHook,
    BaseStateLoader,
):
    """Tracker to track locally -- goes along with the Burr UI. Writes
    down the following:
    #. The whole application + debugging information (e.g. source code) to a file
    #. A line for the start/end of each step
    """

    GRAPH_FILENAME = "graph.json"
    METADATA_FILENAME = "metadata.json"
    LOG_FILENAME = "log.jsonl"
    DEFAULT_STORAGE_DIR = "~/.burr"

    def __init__(
        self,
        project: str,
        storage_dir: str = DEFAULT_STORAGE_DIR,
    ):
        """Instantiates a local tracking client. This will create the following directories, if they don't exist:
        #. The base directory (defaults to ~/.burr)
        #. The project directory (defaults to ~/.burr/<project>)
        #. The application directory (defaults to ~/.burr/<project>/<app_id>) on each

        On application create, it will write the state machine to the application directory.
        On pre/post run step, it will write the start/end of each step to the application directory.

        :param project: Project name -- if this already exists it will be used, otherwise it will be created.
        :param storage_dir: Storage directory
        """

        self.f = None
        if not _allowed_project_name(project, on_windows=system.IS_WINDOWS):
            raise ValueError(
                f"Project: {project} is not valid. Project name cannot contain non-alphanumeric (except _ and -) characters."
                "We will be relaxing this restriction later but for now please rename your project!"
            )
        self.storage_dir = LocalTrackingClient.get_storage_path(project, storage_dir)
        self.project_id = project

    @classmethod
    def get_storage_path(cls, project, storage_dir) -> str:
        return str(os.path.join(os.path.expanduser(storage_dir), project))

    @classmethod
    def app_log_exists(
        cls,
        project: str,
        app_id: str,
        storage_dir: str = DEFAULT_STORAGE_DIR,
    ) -> bool:
        """Function to check if state exists for a given project and app_id.

        :param project: the name of the project
        :param app_id: the application instance id
        :param storage_dir: the storage directory.
        :return: True if state exists, False otherwise.
        """
        path = os.path.join(cls.get_storage_path(project, storage_dir), app_id, cls.LOG_FILENAME)
        if not os.path.exists(path):
            return False
        lines = open(path, "r").readlines()
        if len(lines) == 0:
            return False
        return True

    @classmethod
    def load_state(
        cls,
        project: str,
        app_id: str,
        sequence_id: int = -1,
        storage_dir: str = DEFAULT_STORAGE_DIR,
    ) -> tuple[dict, str]:
        """THis is deprecated and will be removed when we migrate over demos. Do not use! Instead use
        the persistence API :py:class:`initialize_from <burr.core.application.ApplicationBuilder.initialize_from>`
        to load state.

        It defaults to loading the last state, but you can supply a sequence number.

        This is a temporary solution -- not particularly ergonomic, and makes assumptions (particularly that
        all logging is in order), which is fine for now. We will be improving this and making it a first-class
        citizen.


        :param project: the name of the project
        :param app_id: the application instance id
        :param sequence_id: the sequence number of the state to load. Defaults to last index (i.e. -1).
        :param storage_dir: the storage directory.
        :return: the state as a dictionary, and the entry point as a string.
        """
        if sequence_id is None:
            sequence_id = -1  # get the last one
        path = os.path.join(cls.get_storage_path(project, storage_dir), app_id, cls.LOG_FILENAME)
        if not os.path.exists(path):
            raise ValueError(f"No logs found for {project}/{app_id} under {storage_dir}")
        with open(path, "r") as f:
            json_lines = f.readlines()
        # load as JSON
        json_lines = [json.loads(js_line) for js_line in json_lines]
        # filter to only end_entry
        json_lines = [js_line for js_line in json_lines if js_line["type"] == "end_entry"]
        try:
            line = json_lines[sequence_id]
        except IndexError:
            raise ValueError(f"Sequence number {sequence_id} not found for {project}/{app_id}.")
        # check sequence number matches if non-negative; will break if either is None.
        line_seq = int(line["sequence_id"])
        if -1 < sequence_id != line_seq:
            logger.warning(
                f"Sequence number mismatch. For {project}/{app_id}: "
                f"actual:{line_seq} != expected:{sequence_id}"
            )
        # get the prior state
        prior_state = line["state"]
        entry_point = line["action"]
        # delete internally stuff. We can't loop over the keys and delete them in the same loop
        to_delete = []
        for key in prior_state.keys():
            # remove any internal "__" state
            if key.startswith("__"):
                to_delete.append(key)
        for key in to_delete:
            del prior_state[key]
        prior_state["__SEQUENCE_ID"] = line_seq  # add the sequence id back
        return prior_state, entry_point

    def _ensure_dir_structure(self, app_id: str):
        if not os.path.exists(self.storage_dir):
            logger.info(f"Creating storage directory: {self.storage_dir}")
            os.makedirs(self.storage_dir)
        application_path = os.path.join(self.storage_dir, app_id)
        if not os.path.exists(application_path):
            logger.info(f"Creating application directory: {application_path}")
            os.makedirs(application_path)

    def post_application_create(
        self,
        *,
        app_id: str,
        partition_key: Optional[str],
        state: "State",
        application_graph: "ApplicationGraph",
        **future_kwargs: Any,
    ):
        self._ensure_dir_structure(app_id)
        self.f = open(os.path.join(self.storage_dir, app_id, self.LOG_FILENAME), "a")
        graph_path = os.path.join(self.storage_dir, app_id, self.GRAPH_FILENAME)
        if os.path.exists(graph_path):
            logger.info(f"Graph already exists at {graph_path}. Not overwriting.")
            return
        graph = ApplicationModel.from_application_graph(application_graph).model_dump()
        with open(graph_path, "w") as f:
            json.dump(graph, f)

        metadata_path = os.path.join(self.storage_dir, app_id, self.METADATA_FILENAME)
        if os.path.exists(metadata_path):
            logger.info(f"Metadata already exists at {metadata_path}. Not overwriting.")
            return
        metadata = ApplicationMetadataModel(
            partition_key=partition_key,
        ).model_dump()
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

    def _append_write_line(self, model: pydantic.BaseModel):
        self.f.write(model.model_dump_json() + "\n")
        self.f.flush()

    def pre_run_step(
        self,
        state: State,
        action: Action,
        inputs: Dict[str, Any],
        sequence_id: int,
        **future_kwargs: Any,
    ):
        pre_run_entry = BeginEntryModel(
            start_time=datetime.datetime.now(),
            action=action.name,
            inputs=inputs,
            sequence_id=sequence_id,
        )
        self._append_write_line(pre_run_entry)

    def post_run_step(
        self,
        state: State,
        action: Action,
        result: Optional[dict],
        sequence_id: int,
        exception: Exception,
        **future_kwargs: Any,
    ):
        post_run_entry = EndEntryModel(
            end_time=datetime.datetime.now(),
            action=action.name,
            result=result,
            sequence_id=sequence_id,
            exception=_format_exception(exception),
            state=state.get_all(),
        )
        self._append_write_line(post_run_entry)

    def pre_start_span(
        self,
        *,
        action: str,
        sequence_id: int,
        span: ActionSpan,
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        being_span_model = BeginSpanModel(
            start_time=datetime.datetime.now(),
            action_sequence_id=sequence_id,
            span_id=span.uid,
            parent_span_id=span.parent.uid if span.parent else None,
            span_dependencies=span_dependencies,
            span_name=span.name,
        )
        self._append_write_line(being_span_model)

    def post_end_span(
        self,
        *,
        action: str,
        sequence_id: int,
        span: ActionSpan,
        span_dependencies: list[str],
        **future_kwargs: Any,
    ):
        end_span_model = EndSpanModel(
            end_time=datetime.datetime.now(),
            action_sequence_id=sequence_id,
            span_id=span.uid,
        )
        self._append_write_line(end_span_model)

    def __del__(self):
        if self.f is not None:
            self.f.close()

    def list_app_ids(self, partition_key: str, **kwargs) -> list[str]:
        # TODO:
        return []

    def load(
        self, partition_key: str, app_id: Optional[str], sequence_id: Optional[int] = None, **kwargs
    ) -> Optional[PersistedStateData]:
        # TODO:
        if app_id is None:
            return  # no application ID
        if sequence_id is None:
            sequence_id = -1  # get the last one
        path = os.path.join(self.storage_dir, app_id, self.LOG_FILENAME)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            json_lines = f.readlines()
        if len(json_lines) == 0:
            return None  # in this case we have not logged anything yet
        # load as JSON
        json_lines = [json.loads(js_line) for js_line in json_lines]
        # filter to only end_entry
        json_lines = [js_line for js_line in json_lines if js_line["type"] == "end_entry"]
        try:
            line = json_lines[sequence_id]
        except IndexError:
            raise ValueError(
                f"Sequence number {sequence_id} not found for {self.project_id}/{app_id}."
            )
        # check sequence number matches if non-negative; will break if either is None.
        line_seq = int(line["sequence_id"])
        if -1 < sequence_id != line_seq:
            logger.warning(
                f"Sequence number mismatch. For {self.project_id}/{app_id}: "
                f"actual:{line_seq} != expected:{sequence_id}"
            )
        # get the prior state
        prior_state = line["state"]
        position = line["action"]
        # delete internally stuff. We can't loop over the keys and delete them in the same loop
        to_delete = []
        for key in prior_state.keys():
            # remove any internal "__" state
            if key.startswith("__"):
                to_delete.append(key)
        for key in to_delete:
            del prior_state[key]
        prior_state["__SEQUENCE_ID"] = line_seq  # add the sequence id back
        return {
            "partition_key": partition_key,
            "app_id": app_id,
            "sequence_id": line_seq,
            "position": position,
            "state": State(prior_state),
            "created_at": datetime.datetime.fromtimestamp(os.path.getctime(path)).isoformat(),
            "status": "completed" if line["exception"] is None else "failed",
        }


# TODO -- implement async version
# class AsyncTrackingClient(PreRunStepHookAsync, PostRunStepHookAsync, PostApplicationCreateHook):
#     def post_application_create(self, *, state: State, state_graph: ApplicationGraph, **future_kwargs: Any):
#         pass
#
#     async def pre_run_step(self, *, state: State, action: Action, **future_kwargs: Any):
#         raise NotImplementedError(f"TODO: {self.__class__.__name__}.pre_run_step")
#
#     async def post_run_step(self, *, state: State, action: Action, result: Optional[dict], exception: Exception, **future_kwargs: Any):
#         raise NotImplementedError(f"TODO: {self.__class__.__name__}.pre_run_step")
#
