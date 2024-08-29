import abc
import collections
import importlib
import json
import os.path
import sys
from typing import Any, Optional, Sequence, Tuple, Type, TypeVar

import aiofiles
import aiofiles.os as aiofilesos
import fastapi
from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict

from burr.tracking.common import models
from burr.tracking.common.models import ChildApplicationModel
from burr.tracking.server import schema
from burr.tracking.server.schema import ApplicationLogs, ApplicationSummary, Step

T = TypeVar("T")

# The following is a backend for the server.
# Note this is not a fixed API yet, and thus not documented (in Burr's documentation)
# Specifically, this does not have:
# - Streaming returns (just log tails)
# - Pagination
# - Authentication/Authorization


if sys.version_info <= (3, 11):
    Self = Any
else:
    from typing import Self


class BurrSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="burr_")


class IndexingBackendMixin(abc.ABC):
    """Base mixin for an indexing backend -- one that index from
    logs (E.G. s3)"""

    @abc.abstractmethod
    async def update(self):
        """Updates the index"""
        pass

    @abc.abstractmethod
    async def update_interval_milliseconds(self) -> Optional[int]:
        """Returns the update interval in milliseconds"""
        pass

    @abc.abstractmethod
    async def indexing_jobs(
        self, offset: int = 0, limit: int = 100, filter_empty: bool = True
    ) -> Sequence[schema.IndexingJob]:
        """Returns the indexing jobs"""
        pass


class SnapshottingBackendMixin(abc.ABC):
    """Mixin for backend that conducts snapshotting -- e.g. saves
    the data to a file or database."""

    @abc.abstractmethod
    async def load_snapshot(self):
        """Loads the snapshot if it exists.

        :return:
        """
        pass

    @abc.abstractmethod
    async def snapshot(self):
        """Snapshots the data"""
        pass

    @abc.abstractmethod
    def snapshot_interval_milliseconds(self) -> Optional[int]:
        """Returns the snapshot interval in milliseconds"""
        pass


class BackendBase(abc.ABC):
    async def lifespan(self, app: FastAPI):
        """Quick tool to allow plugin to the app's lifecycle.
        This is fine given that it's an internal API, but if we open it up more
        we should make this less flexible. For now this allows us to do clever
        initializations in the right order."""
        yield

    @abc.abstractmethod
    async def list_projects(self, request: fastapi.Request) -> Sequence[schema.Project]:
        """Lists out all projects -- this relies on the paginate function to work properly.

        :param request: The request object, used for authentication/authorization if needed
        :return: the next page
        """
        pass

    @abc.abstractmethod
    async def list_apps(
        self,
        request: fastapi.Request,
        project_id: str,
        partition_key: Optional[str],
        limit: int,
        offset: int,
    ) -> Tuple[Sequence[schema.ApplicationSummary], int]:
        """Lists out all apps (continual state machine runs with shared state) for a given project.

        :param request: The request object, used for authentication/authorization if needed
        :param project_id: filter by project id
        :param partition_key: filter by partition key
        :return: A list of apps and the total number of apps (given that we paginate)
        """
        pass

    @abc.abstractmethod
    async def get_application_logs(
        self, request: fastapi.Request, project_id: str, app_id: str, partition_key: Optional[str]
    ) -> ApplicationLogs:
        """Lists out all steps for a given app.

        :param request: The request object, used for authentication/authorization if needed
        :param app_id:
        :return:
        """
        pass

    @classmethod
    @abc.abstractmethod
    def settings_model(cls) -> Type[BaseSettings]:
        """Gives a settings model that tells us how to configure the backend.
        This is a class of pydantic BaseSettings type

        :return:  the settings model
        """
        pass

    @classmethod
    def from_settings(cls, settings_model: BaseSettings) -> Self:
        """Creates a backend from settings, of the type of settings_model above
        This defaults to assuming the constructor takes in settings parameters

        :param settings_model:
        :return:
        """
        return cls(**settings_model.dict())

    @classmethod
    def create_from_env(cls, dotenv_path: Optional[str] = None) -> Self:
        cls_path = os.environ.get("BURR_BACKEND_IMPL", "burr.tracking.server.backend.LocalBackend")
        mod_path = ".".join(cls_path.split(".")[:-1])
        mod = importlib.import_module(mod_path)
        cls_name = cls_path.split(".")[-1]
        if not hasattr(mod, cls_name):
            raise ValueError(f"Could not find {cls_name} in {mod_path}")
        cls = getattr(mod, cls_name)
        return cls.from_settings(
            cls.settings_model()(_env_file=dotenv_path, _env_file_encoding="utf-8")
        )

    def supports_demos(self) -> bool:
        """Whether this supports demos. Really we should abstract this out into a new mixin
        but for now this is OK.
        """
        return False


def safe_json_load(line: bytes):
    # Every once in a while we'll hit a non-utf-8 character
    # In this case we replace it and hope for the best
    return json.loads(line.decode("utf-8", errors="replace"))


def get_uri(project_id: str) -> str:
    project_id_map = {
        "demo_counter": "https://github.com/DAGWorks-Inc/burr/tree/main/examples/hello-world-counter",
        "demo_tracing": "https://github.com/DAGWorks-Inc/burr/tree/main/examples/tracing-and-spans/application.py",
        "demo_chatbot": "https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-modal-chatbot",
        "demo_conversational-rag": "https://github.com/DAGWorks-Inc/burr/tree/main/examples/conversational-rag",
    }
    return project_id_map.get(project_id, "")


DEFAULT_PATH = os.path.expanduser("~/.burr")


class LocalBackend(BackendBase):
    """Quick implementation of a local backend for testing purposes. This is not a production backend."""

    # TODO -- make this configurable through an env variable

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
                        uri=get_uri(entry),
                        last_written=await aiofilesos.path.getmtime(full_path),
                        created=await aiofilesos.path.getctime(full_path),
                        num_apps=len(await aiofilesos.listdir(full_path)),
                    )
                )
        return out

    async def get_number_of_steps(self, file_path: str) -> int:
        """Quick tool to get the latest sequence ID from a log file.
        This is not efficient and should be replaced."""
        async with aiofiles.open(file_path, "rb") as f:
            for line in reversed(await f.readlines()):
                line_data = safe_json_load(line)
                if "sequence_id" in line_data:
                    # Just return the latest we can determine for now
                    # We add one as it is the count, not the index
                    return line_data["sequence_id"] + 1
        return 0

    async def _load_metadata(self, metadata_path: str) -> models.ApplicationMetadataModel:
        if os.path.exists(metadata_path):
            async with aiofiles.open(metadata_path, "rb") as f:
                raw = await f.read()
                return models.ApplicationMetadataModel.parse_obj(safe_json_load(raw))
        return models.ApplicationMetadataModel()

    async def list_apps(
        self,
        request: fastapi.Request,
        project_id: str,
        partition_key: Optional[str],
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[Sequence[ApplicationSummary], int]:
        project_filepath = os.path.join(self.path, project_id)
        if not os.path.exists(project_filepath):
            return [], 0
            # raise fastapi.HTTPException(status_code=404, detail=f"Project: {project_id} not found")
        out = []
        for entry in await aiofilesos.listdir(project_filepath):
            if entry.startswith("."):
                # skip hidden files/directories
                continue
            full_path = os.path.join(project_filepath, entry)
            metadata_path = os.path.join(full_path, "metadata.json")
            log_path = os.path.join(full_path, "log.jsonl")
            if os.path.isdir(full_path):
                metadata = await self._load_metadata(metadata_path)
                app_partition_key = metadata.partition_key
                # quick, hacky way to do it -- we should really have this be part of the path
                # But we load it up anyway. TODO -- add partition key to the path
                # If this is slow you'll want to use the s3-based storage system
                # Which has an actual index
                if partition_key is not None and partition_key != app_partition_key:
                    continue
                out.append(
                    schema.ApplicationSummary(
                        app_id=entry,
                        partition_key=metadata.partition_key,
                        first_written=await aiofilesos.path.getctime(full_path),
                        last_written=await aiofilesos.path.getmtime(full_path),
                        num_steps=await self.get_number_of_steps(log_path),
                        tags={},
                        parent_pointer=metadata.parent_pointer,
                        spawning_parent_pointer=metadata.spawning_parent_pointer,
                    )
                )
        out = sorted(out, key=lambda x: x.last_written, reverse=True)
        # TODO -- actually only get the most recent ones rather than reading everything, this is inefficient
        return out[offset : offset + limit], len(out)

    async def get_application_logs(
        self, request: fastapi.Request, project_id: str, app_id: str, partition_key: Optional[str]
    ) -> ApplicationLogs:
        # TODO -- handle partition key here
        # This currently assumes uniqueness
        app_filepath = os.path.join(self.path, project_id, app_id)
        if not os.path.exists(app_filepath):
            raise fastapi.HTTPException(
                status_code=404, detail=f"App: {app_id} from project: {project_id} not found"
            )
        log_file = os.path.join(app_filepath, "log.jsonl")
        graph_file = os.path.join(app_filepath, "graph.json")
        metadata_file = os.path.join(app_filepath, "metadata.json")
        children_file = os.path.join(app_filepath, "children.jsonl")
        metadata = await self._load_metadata(metadata_file)
        if not os.path.exists(graph_file):
            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Graph file for app: {app_id} from project: {project_id} not found",
            )
        async with aiofiles.open(graph_file) as f:
            str_graph = await f.read()
        collections.defaultdict(list)
        if os.path.exists(log_file):
            async with aiofiles.open(log_file, "rb") as f:
                lines = await f.readlines()
                steps = Step.from_logs(lines)
        children = []
        if os.path.exists(children_file):
            async with aiofiles.open(children_file) as f:
                str_children = await f.readlines()
                children = [
                    ChildApplicationModel.parse_obj(json.loads(item)) for item in str_children
                ]

        return ApplicationLogs(
            application=schema.ApplicationModel.parse_raw(str_graph),
            steps=steps,
            parent_pointer=metadata.parent_pointer,
            spawning_parent_pointer=metadata.spawning_parent_pointer,
            children=children,
        )

    def supports_demos(self) -> bool:
        return True

    class BackendSettings(BurrSettings):
        path: str = DEFAULT_PATH

    @classmethod
    def settings_model(cls) -> Type[BurrSettings]:
        return cls.BackendSettings

    @classmethod
    def from_settings(cls, settings_model: BurrSettings) -> Self:
        return cls(**settings_model.dict())
