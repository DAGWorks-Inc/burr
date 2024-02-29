import datetime
import json
import logging
import os
import traceback
import uuid
from typing import Any, Dict, Optional

from burr.core import Action, ApplicationGraph, State
from burr.integrations.base import require_plugin
from burr.lifecycle import PostRunStepHook, PreRunStepHook
from burr.lifecycle.base import PostApplicationCreateHook
from burr.tracking.common.models import ApplicationModel, BeginEntryModel, EndEntryModel

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


class LocalTrackingClient(PostApplicationCreateHook, PreRunStepHook, PostRunStepHook):
    """Tracker to track locally -- goes along with the Burr UI. Writes
    down the following:
    #. The whole application + debugging information (e.g. source code) to a file
    #. A line for the start/end of each step
    """

    GRAPH_FILENAME = "graph.json"
    LOG_FILENAME = "log.jsonl"
    DEFAULT_STORAGE_DIR = "~/.burr"

    def __init__(
        self,
        project: str,
        storage_dir: str = DEFAULT_STORAGE_DIR,
        app_id: Optional[str] = None,
    ):
        """Instantiates a local tracking client. This will create the following directories, if they don't exist:
        #. The base directory (defaults to ~/.burr)
        #. The project directory (defaults to ~/.burr/<project>)
        #. The application directory (defaults to ~/.burr/<project>/<app_id>) on each

        On application create, it will write the state machine to the application directory.
        On pre/post run step, it will write the start/end of each step to the application directory.

        :param project: Project name -- if this already exists it will be used, otherwise it will be created.
        :param storage_dir: Storage directory
        :param app_id: Unique application ID. If not provided, a random one will be generated. If this already exists,
            it will use that one/append to the files in that one.
        """
        if app_id is None:
            app_id = f"app_{str(uuid.uuid4())}"
        storage_dir = self.get_storage_path(project, storage_dir)
        self.app_id = app_id
        self.storage_dir = storage_dir
        self._ensure_dir_structure()
        self.f = open(os.path.join(self.storage_dir, self.app_id, self.LOG_FILENAME), "a")

    @staticmethod
    def get_storage_path(project, storage_dir):
        return os.path.join(os.path.expanduser(storage_dir), project)

    @classmethod
    def get_state(
        cls,
        project: str,
        app_id: str,
        sequence_no: int = -1,
        storage_dir: str = DEFAULT_STORAGE_DIR,
    ) -> tuple[dict, str]:
        """Initialize the state to debug from an exception.

        :param project:
        :param app_id:
        :param sequence_no:
        :param storage_dir:
        :return:
        """
        if sequence_no is None:
            sequence_no = -1  # get the last one
        path = os.path.join(cls.get_storage_path(project, storage_dir), app_id, cls.LOG_FILENAME)
        if not os.path.exists(path):
            raise ValueError(f"No logs found for {project}/{app_id} under {storage_dir}")
        with open(path, "r") as f:
            json_lines = f.readlines()
        json_lines = [json.loads(js_line) for js_line in json_lines]
        json_lines = [js_line for js_line in json_lines if js_line["type"] == "end_entry"]
        line = {}
        if sequence_no < 0:
            line = json_lines[sequence_no]
        else:
            found_line = False
            for line in json_lines:
                if line["sequence_no"] == sequence_no:
                    found_line = True
                    break
            if not found_line:
                raise ValueError(f"Sequence number {sequence_no} not found for {project}/{app_id}.")
        state = line["state"]
        to_delete = []
        for key in state.keys():
            if key.startswith("__"):
                to_delete.append(key)
        for key in to_delete:
            del state[key]
        entry_point = line["action"]
        return state, entry_point

    def _ensure_dir_structure(self):
        if not os.path.exists(self.storage_dir):
            logger.info(f"Creating storage directory: {self.storage_dir}")
            os.makedirs(self.storage_dir)
        application_path = os.path.join(self.storage_dir, self.app_id)
        if not os.path.exists(application_path):
            logger.info(f"Creating application directory: {application_path}")
            os.makedirs(application_path)

    def post_application_create(
        self, *, state: "State", application_graph: "ApplicationGraph", **future_kwargs: Any
    ):
        path = os.path.join(self.storage_dir, self.app_id, self.GRAPH_FILENAME)
        if os.path.exists(path):
            logger.info(f"Graph already exists at {path}. Not overwriting.")
            return
        graph = ApplicationModel.from_application_graph(application_graph).model_dump()
        with open(path, "w") as f:
            json.dump(graph, f)

    def _append_write_line(self, model: pydantic.BaseModel):
        self.f.write(model.model_dump_json() + "\n")
        self.f.flush()

    def pre_run_step(
        self, *, state: State, action: Action, inputs: Dict[str, Any], **future_kwargs: Any
    ):
        pre_run_entry = BeginEntryModel(
            start_time=datetime.datetime.now(),
            action=action.name,
            inputs=inputs,
        )
        self._append_write_line(pre_run_entry)

    def post_run_step(
        self,
        *,
        state: State,
        action: Action,
        result: Optional[dict],
        exception: Exception,
        **future_kwargs: Any,
    ):
        post_run_entry = EndEntryModel(
            end_time=datetime.datetime.now(),
            action=action.name,
            result=result,
            exception=_format_exception(exception),
            state=state.get_all(),
        )
        self._append_write_line(post_run_entry)

    def __del__(self):
        self.f.close()


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
