import abc
import json
import os.path
from typing import Sequence, TypeVar

import aiofiles
import aiofiles.os as aiofilesos
import fastapi

from burr.tracking.common.models import BeginEntryModel, BeginSpanModel, EndEntryModel, EndSpanModel
from burr.tracking.server import schema
from burr.tracking.server.schema import ApplicationLogs, ApplicationSummary

T = TypeVar("T")


# The following is a backend for the server.
# Note this is not a fixed API yet, and thus not documented (in Burr's documentation)
# Specifically, this does not have:
# - Streaming returns (just log tails)
# - Pagination
# - Authentication/Authorization


class BackendBase(abc.ABC):
    @abc.abstractmethod
    async def list_projects(self, request: fastapi.Request) -> Sequence[schema.Project]:
        """Lists out all projects -- this relies on the paginate function to work properly.

        :param request: The request object, used for authentication/authorization if needed
        :return: the next page
        """
        pass

    @abc.abstractmethod
    async def list_apps(
        self, request: fastapi.Request, project_id: str
    ) -> Sequence[schema.ApplicationSummary]:
        """Lists out all apps (continual state machine runs with shared state) for a given project.

        :param request: The request object, used for authentication/authorization if needed
        :param project_id:
        :return:
        """
        pass

    @abc.abstractmethod
    async def get_application_logs(
        self, request: fastapi.Request, project_id: str, app_id: str
    ) -> Sequence[schema.Step]:
        """Lists out all steps for a given app.

        :param request: The request object, used for authentication/authorization if needed
        :param app_id:
        :return:
        """
        pass


class LocalBackend(BackendBase):
    """Quick implementation of a local backend for testing purposes. This is not a production backend."""

    # TODO -- make this configurable through an env variable
    DEFAULT_PATH = os.path.expanduser("~/.burr")

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path

    async def list_projects(self, request: fastapi.Request) -> Sequence[schema.Project]:
        out = []
        if not os.path.exists(self.path):
            return out
        for entry in await aiofilesos.listdir(self.path):
            full_path = os.path.join(self.path, entry)
            if os.path.isdir(full_path):
                out.append(
                    schema.Project(
                        name=entry,
                        id=entry,
                        uri=full_path,  # TODO -- figure out what
                        last_written=await aiofilesos.path.getmtime(full_path),
                        created=await aiofilesos.path.getctime(full_path),
                        num_apps=len(await aiofilesos.listdir(full_path)),
                    )
                )
        return out

    async def get_max_sequence_id(self, file_path: str) -> int:
        """Quick tool to get the latest sequence ID from a log file.
        This is not efficient and should be replaced."""
        count = 0
        async with aiofiles.open(file_path, "rb") as f:
            for line in reversed(await f.readlines()):
                line_data = json.loads(line)
                if "sequence_id" in line_data:
                    # Just return the latest for now
                    return line_data["sequence_id"]
        return count

    async def list_apps(
        self, request: fastapi.Request, project_id: str
    ) -> Sequence[ApplicationSummary]:
        project_filepath = os.path.join(self.path, project_id)
        if not os.path.exists(project_filepath):
            raise fastapi.HTTPException(status_code=404, detail=f"Project: {project_id} not found")
        out = []
        for entry in await aiofilesos.listdir(project_filepath):
            if entry.startswith("."):
                # skip hidden files/directories
                continue
            full_path = os.path.join(project_filepath, entry)
            log_path = os.path.join(full_path, "log.jsonl")
            if os.path.isdir(full_path):
                out.append(
                    schema.ApplicationSummary(
                        app_id=entry,
                        first_written=await aiofilesos.path.getctime(full_path),
                        last_written=await aiofilesos.path.getmtime(full_path),
                        num_steps=await self.get_max_sequence_id(log_path),
                        tags={},
                    )
                )
        return out

    async def get_application_logs(
        self, request: fastapi.Request, project_id: str, app_id: str
    ) -> ApplicationLogs:
        app_filepath = os.path.join(self.path, project_id, app_id)
        if not os.path.exists(app_filepath):
            raise fastapi.HTTPException(
                status_code=404, detail=f"App: {app_id} from project: {project_id} not found"
            )
        log_file = os.path.join(app_filepath, "log.jsonl")
        graph_file = os.path.join(app_filepath, "graph.json")
        if not os.path.exists(graph_file):
            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Graph file not found for app: "
                f"{app_id} from project: {project_id}. "
                f"Was this properly executed?",
            )
        steps_by_sequence_id = {}
        spans_by_id = {}
        if os.path.exists(log_file):
            async with aiofiles.open(log_file) as f:
                for line in await f.readlines():
                    json_line = json.loads(line)
                    # TODO -- make these into constants
                    if json_line["type"] == "begin_entry":
                        begin_step = BeginEntryModel.parse_obj(json_line)
                        steps_by_sequence_id[begin_step.sequence_id] = schema.Step(
                            step_start_log=begin_step, step_end_log=None, spans=[]
                        )
                    elif json_line["type"] == "end_entry":
                        # this assumes they'll be in order
                        step_end_log = EndEntryModel.parse_obj(json_line)
                        step = steps_by_sequence_id[step_end_log.sequence_id]
                        step.step_end_log = step_end_log
                    elif json_line["type"] == "begin_span":
                        span = BeginSpanModel.parse_obj(json_line)
                        spans_by_id[span.span_id] = schema.Span(
                            begin_entry=span,
                            end_entry=None,
                        )
                    elif json_line["type"] == "end_span":
                        end_span = EndSpanModel.parse_obj(json_line)
                        span = spans_by_id[end_span.span_id]
                        span.end_entry = end_span
        for span in spans_by_id.values():
            step = steps_by_sequence_id[span.begin_entry.action_sequence_id]
            step.spans.append(span)
        async with aiofiles.open(graph_file) as f:
            str_graph = await f.read()
        return ApplicationLogs(
            application=schema.ApplicationModel.parse_raw(str_graph),
            steps=list(steps_by_sequence_id.values()),
        )
