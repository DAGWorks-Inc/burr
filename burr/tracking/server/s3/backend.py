import dataclasses
import datetime
import functools
import itertools
import json
import logging
import operator
import os.path
import sys
import uuid
from collections import Counter
from typing import List, Literal, Optional, Sequence, Tuple, Type, TypeVar, Union

import fastapi
import pydantic
from aiobotocore import session
from fastapi import FastAPI
from pydantic_settings import BaseSettings
from tortoise import functions, transactions
from tortoise.contrib.fastapi import RegisterTortoise
from tortoise.expressions import Q

from burr.tracking.common.models import ApplicationModel
from burr.tracking.server import schema
from burr.tracking.server.backend import (
    BackendBase,
    BurrSettings,
    IndexingBackendMixin,
    SnapshottingBackendMixin,
)
from burr.tracking.server.s3 import settings, utils
from burr.tracking.server.s3.models import (
    Application,
    IndexingJob,
    IndexingJobStatus,
    IndexStatus,
    LogFile,
    Project,
)
from burr.tracking.server.schema import ApplicationLogs, Step

logger = logging.getLogger(__name__)

FileType = Literal["log", "metadata", "graph"]

ContentsModel = TypeVar("ContentsModel", bound=pydantic.BaseModel)

if sys.version_info >= (3, 11):
    utc = datetime.UTC
else:
    utc = datetime.timezone.utc


async def _query_s3_file(
    bucket: str,
    key: str,
    client: session.AioBaseClient,
) -> Union[ContentsModel, List[ContentsModel]]:
    response = await client.get_object(Bucket=bucket, Key=key)
    body = await response["Body"].read()
    return body


@dataclasses.dataclass
class DataFile:
    """Generic data file object meant to represent a file in the s3 bucket. This has a few possible roles (log, metadata, and graph file)"""

    prefix: str
    yyyy: str
    mm: str
    dd: str
    hh: str
    minutes_string: str
    partition_key: str
    application_id: str
    file_type: FileType
    path: str
    created_date: datetime.datetime

    @classmethod
    def from_path(cls, path: str, created_date: datetime.datetime) -> "DataFile":
        parts = path.split("/")

        # Validate that there are enough parts to extract the needed fields
        if len(parts) < 9:
            raise ValueError(f"Path '{path}' is not valid")

        prefix = "/".join(parts[:-8])  # Everything before the year part
        yyyy = parts[2]
        mm = parts[3]
        dd = parts[4]
        hh = parts[5]
        minutes_string = parts[6]
        application_id = parts[8]
        partition_key = parts[7]
        filename = parts[9]
        file_type = (
            "graph"
            if filename.endswith("graph.json")
            else "metadata"
            if filename.endswith("_metadata.json")
            else "log"
        )

        # # Validate the date parts
        # if not (yyyy.isdigit() and mm.isdigit() and dd.isdigit() and hh.isdigit()):
        #     raise ValueError(f"Date components in the path '{path}' are not valid")

        return cls(
            prefix=prefix,
            yyyy=yyyy,
            mm=mm,
            dd=dd,
            hh=hh,
            minutes_string=minutes_string,
            application_id=application_id,
            partition_key=partition_key,
            file_type=file_type,
            path=path,
            created_date=created_date,
        )


class S3Settings(BurrSettings):
    s3_bucket: str
    update_interval_milliseconds: int = 120_000
    aws_max_concurrency: int = 100
    snapshot_interval_milliseconds: int = 3_600_000
    load_snapshot_on_start: bool = True
    prior_snapshots_to_keep: int = 5


def timestamp_to_reverse_alphabetical(timestamp: datetime) -> str:
    # Get the inverse of the timestamp
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    total_seconds = int((timestamp - epoch).total_seconds())

    # Invert the seconds (latest timestamps become smallest values)
    inverted_seconds = 2**32 - total_seconds

    # Convert the inverted seconds to a zero-padded string
    inverted_str = str(inverted_seconds).zfill(10)

    return inverted_str + "-" + timestamp.isoformat()


class SQLiteS3Backend(BackendBase, IndexingBackendMixin, SnapshottingBackendMixin):
    def __init__(
        self,
        s3_bucket: str,
        update_interval_milliseconds: int,
        aws_max_concurrency: int,
        snapshot_interval_milliseconds: int,
        load_snapshot_on_start: bool,
        prior_snapshots_to_keep: int,
    ):
        self._backend_id = datetime.datetime.now(utc).isoformat() + str(uuid.uuid4())
        self._bucket = s3_bucket
        self._session = session.get_session()
        self._update_interval_milliseconds = update_interval_milliseconds
        self._aws_max_concurrency = aws_max_concurrency
        self._snapshot_interval_milliseconds = snapshot_interval_milliseconds
        self._data_prefix = "data"
        self._snapshot_prefix = "snapshots"
        self._load_snapshot_on_start = load_snapshot_on_start
        self._snapshot_key_history = []
        self._prior_snapshots_to_keep = prior_snapshots_to_keep

    async def load_snapshot(self):
        if not self._load_snapshot_on_start:
            return
        path = settings.DB_PATH
        # if it already exists then return
        if os.path.exists(path):
            return
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        async with self._session.create_client("s3") as client:
            objects = await client.list_objects_v2(
                Bucket=self._bucket, Prefix=self._snapshot_prefix, MaxKeys=1
            )
            if objects["KeyCount"] == 0:
                return
            # get the latest snapshot -- it's organized by alphabetical order
            latest_snapshot = objects["Contents"][0]
            # download the snapshot
            response = await client.get_object(Bucket=self._bucket, Key=latest_snapshot["Key"])
            async with response["Body"] as stream:
                with open(path, "wb") as file:
                    file.write(await stream.read())

    def snapshot_interval_milliseconds(self) -> Optional[int]:
        return self._snapshot_interval_milliseconds

    @classmethod
    def settings_model(cls) -> Type[BaseSettings]:
        return S3Settings

    async def snapshot(self):
        path = settings.DB_PATH
        timestamp = timestamp_to_reverse_alphabetical(datetime.datetime.now(datetime.UTC))
        # latest
        s3_key = f"{self._snapshot_prefix}/{timestamp}/{self._backend_id}/snapshot.db"
        # TODO -- copy the path at snapshot_path to s3 using aiobotocore
        session = self._session
        logger.info(f"Saving db snapshot at: {s3_key}")
        async with session.create_client("s3") as s3_client:
            with open(path, "rb") as file_data:
                await s3_client.put_object(Bucket=self._bucket, Key=s3_key, Body=file_data)

        self._snapshot_key_history.append(s3_key)
        if len(self._snapshot_key_history) > 5:
            old_snapshot_to_remove = self._snapshot_key_history.pop(0)
            logger.info(f"Removing old snapshot: {old_snapshot_to_remove}")
            async with session.create_client("s3") as s3_client:
                await s3_client.delete_object(Bucket=self._bucket, Key=old_snapshot_to_remove)

    def update_interval_milliseconds(self) -> Optional[int]:
        return self._update_interval_milliseconds

    async def _s3_get_first_write_date(self, project_id: str):
        async with self._session.create_client("s3") as client:
            paginator = client.get_paginator("list_objects_v2")
            async for result in paginator.paginate(
                Bucket=self._bucket,
                Prefix=f"{self._data_prefix}/{project_id}/",
                Delimiter="/",
                MaxKeys=1,
            ):
                if "Contents" in result:
                    first_object = result["Contents"][0]
                    return first_object["LastModified"]
        return (
            datetime.datetime.utcnow()
        )  # This should never be hit unless someone is concurrently deleting...

    async def _update_projects(self):
        current_projects = await Project.all()
        project_names = {project.name for project in current_projects}
        logger.info(f"Current projects: {project_names}")
        async with self._session.create_client("s3") as client:
            paginator = client.get_paginator("list_objects_v2")
            async for result in paginator.paginate(
                Bucket=self._bucket, Prefix=f"{self._data_prefix}/", Delimiter="/"
            ):
                for prefix in result.get("CommonPrefixes", []):
                    project_name = prefix.get("Prefix").split("/")[-2]
                    if project_name not in project_names:
                        now = datetime.datetime.utcnow()
                        logger.info(f"Creating project: {project_name}")
                        await Project.create(
                            name=project_name,
                            uri=None,
                            created_at=await self._s3_get_first_write_date(project_id=project_name),
                            indexed_at=now,
                            updated_at=now,
                        )

    async def query_applications_by_key(
        self, application_keys: Sequence[tuple[str, Optional[str]]]
    ):
        conditions = [
            Q(name=app_id, partition_key=partition_key)
            for app_id, partition_key in application_keys
        ]

        # Combine the conditions with an OR operation
        query = Application.filter(functools.reduce(operator.or_, conditions))

        # Execute the query
        applications = await query.all()
        return applications

    async def _gather_metadata_files(
        self,
        metadata_files: List[DataFile],
    ) -> Sequence[dict]:
        """Gives a list of metadata files so we can update the application"""

        async def _query_metadata_file(metadata_file: DataFile) -> dict:
            async with self._session.create_client("s3") as client:
                response = await client.head_object(
                    Bucket=self._bucket,
                    Key=metadata_file.path,
                )
                # metadata = await response['Body'].read()
                parent_pointer_raw = response["Metadata"].get("parent_pointer")
                spawning_parent_pointer_raw = response["Metadata"].get("spawning_parent_pointer")
                return dict(
                    partition_key=metadata_file.partition_key,
                    parent_pointer=json.loads(parent_pointer_raw)
                    if parent_pointer_raw != "None"
                    else None,
                    spawning_parent_pointer=json.loads(spawning_parent_pointer_raw)
                    if spawning_parent_pointer_raw != "None"
                    else None,
                )

        out = await utils.gather_with_concurrency(
            self._aws_max_concurrency,
            *[_query_metadata_file(metadata_file) for metadata_file in metadata_files],
        )
        return out

    async def _gather_log_file_data(self, log_files: List[DataFile]) -> Sequence[dict]:
        """Gives a list of log files so we can update the application"""

        async def _query_log_file(log_file: DataFile) -> dict:
            async with self._session.create_client("s3") as client:
                response = await client.head_object(
                    Bucket=self._bucket,
                    Key=log_file.path,
                )
                # TODO -- consider the default cases, we should not have them and instead mark this as failed
                return {
                    "min_sequence_id": response["Metadata"].get("min_sequence_id", 0),
                    "max_sequence_id": response["Metadata"].get("max_sequence_id", 0),
                    "tracker_id": response["Metadata"].get("tracker_id", "unknown"),
                }

        out = await utils.gather_with_concurrency(
            self._aws_max_concurrency, *[_query_log_file(log_file) for log_file in log_files]
        )
        return out

    async def _gather_paths_to_update(
        self, project: Project, high_watermark_s3_path: str
    ) -> Sequence[DataFile]:
        """Gathers all paths to update in s3 -- we store file pointers in the db for these.
        This allows us to periodically scan for more files to index.

        :return: list of paths to update
        """
        logger.info(f"Scanning db with highwatermark: {high_watermark_s3_path}")
        paths_to_update = []
        logger.info(f"Scanning log data for project: {project.name}")
        async with self._session.create_client("s3") as client:
            paginator = client.get_paginator("list_objects_v2")
            async for result in paginator.paginate(
                Bucket=self._bucket,
                Prefix=f"{self._data_prefix}/{project.name}/",
                StartAfter=high_watermark_s3_path,
            ):
                for content in result.get("Contents", []):
                    key = content["Key"]
                    last_modified = content["LastModified"]
                    # Created == last_modified as we have an immutable data model
                    logger.info(f"Found new file: {key}")
                    paths_to_update.append(DataFile.from_path(key, created_date=last_modified))
        logger.info(f"Found {len(paths_to_update)} new files to index")
        return paths_to_update

    async def _ensure_applications_exist(
        self, paths_to_update: Sequence[DataFile], project: Project
    ):
        """Given the paths to update, ensure that all corresponding applications exist in the database.

        :param paths_to_update:
        :param project:
        :return:
        """
        all_application_keys = sorted(
            {(path.application_id, path.partition_key) for path in paths_to_update}
        )
        counter = Counter([path.file_type for path in paths_to_update])
        logger.info(
            f"Found {len(all_application_keys)} applications in the scan, "
            f"including: {counter['log']} log files, "
            f"{counter['metadata']} metadata files, and {counter['graph']} graph files, "
            f"and {len(paths_to_update) - len(all_application_keys)} other files."
        )

        # First, let's create all applications, ignoring them if they exist

        # first let's create all the applications if they don't exist
        existing_applications = {
            (app.name, app.partition_key): app
            for app in await self.query_applications_by_key(all_application_keys)
        }
        # all_applications = await Application.all()

        apps_to_create = [
            Application(
                name=app_id,
                partition_key=pk,
                project=project,
                created_at=datetime.datetime.utcnow(),
            )
            for app_id, pk in all_application_keys
            if (app_id, pk) not in existing_applications
        ]

        logger.info(
            f"Creating {len(apps_to_create)} new applications, with keys: {[(app.name, app.partition_key) for app in apps_to_create]}"
        )
        await Application.bulk_create(apps_to_create)
        all_applications = await self.query_applications_by_key(all_application_keys)
        return all_applications

    async def _update_all_applications(
        self, all_applications: Sequence[Application], paths_to_update: Sequence[DataFile]
    ) -> Sequence[Application]:
        """Updates all application with associate metadata and graph files

        :param all_applications: All applications that are relevant
        :param paths_to_update: All paths to update
        :return:
        """
        logger.info(f"found: {len(all_applications)} applications to update in the db")
        metadata_data = [path for path in paths_to_update if path.file_type == "metadata"]
        graph_data = [path for path in paths_to_update if path.file_type == "graph"]
        metadata_objects = await self._gather_metadata_files(metadata_data)
        key_to_application_map = {(app.name, app.partition_key): app for app in all_applications}
        # For every metadata file we want to add the metadata file
        for metadata, datafile in zip(metadata_objects, metadata_data):
            key = (datafile.application_id, datafile.partition_key)
            app = key_to_application_map[key]
            app.metadata_file_pointer = datafile.path

            # TODO -- download the metadata file and update the application

        # for every graph file, we want to add the pointer
        for graph_file in graph_data:
            key = (graph_file.application_id, graph_file.partition_key)
            app = key_to_application_map[key]
            app.graph_file_pointer = graph_file.path
        # Go through every application and save them
        async with transactions.in_transaction():
            # TODO -- look at bulk saving, instead of transactions
            for app in all_applications:
                await app.save()
        return all_applications

    async def update_log_files(
        self, paths_to_update: Sequence[DataFile], all_applications: Sequence[Application]
    ):
        log_data = [path for path in paths_to_update if path.file_type == "log"]
        logfile_objects = await self._gather_log_file_data(log_data)
        key_to_application_map = {(app.name, app.partition_key): app for app in all_applications}

        # TODO -- gather referenced apps (parent pointers) and get the map of IDs to names

        # Go through every log file we've stored and update the appropriate item in the db
        logfiles_to_save = []
        for logfile, datafile in zip(logfile_objects, log_data):
            # get the application for the log file
            app = key_to_application_map[(datafile.application_id, datafile.partition_key)]
            # create the log file object
            logfiles_to_save.append(
                LogFile(
                    s3_path=datafile.path,
                    application=app,
                    tracker_id=logfile["tracker_id"],
                    min_sequence_id=logfile["min_sequence_id"],
                    max_sequence_id=logfile["max_sequence_id"],
                    created_at=datafile.created_date,
                )
            )
        # Save all the log files
        await LogFile.bulk_create(logfiles_to_save)

    async def _update_high_watermark(
        self, paths_to_update: Sequence[DataFile], project: Project, indexing_job: IndexingJob
    ):
        new_high_watermark = max(paths_to_update, key=lambda x: x.path).path
        next_status = IndexStatus(s3_highwatermark=new_high_watermark, project=project)
        await next_status.save()
        return next_status

    async def _scan_and_update_db_for_project(
        self, project: Project, indexing_job: IndexingJob
    ) -> Tuple[IndexStatus, int]:
        """Scans and updates the database for a project.

        TODO -- break this up into functions

        :param project: Project to scan/update
        :param max_length: Maximum length of the scan -- will pause and return after this. This is so we don't block for too long.
        :return: tuple of index status/num files processed
        """
        # get the current status
        current_status = (
            await IndexStatus.filter(project=project).order_by("-captured_time").first()
        )
        # This way we can sort by the latest captured time
        high_watermark = current_status.s3_highwatermark if current_status is not None else ""
        logger.info(f"Scanning db with highwatermark: {high_watermark}")
        paths_to_update = await self._gather_paths_to_update(
            project=project, high_watermark_s3_path=high_watermark
        )
        # Nothing new to see here
        if len(paths_to_update) == 0:
            return current_status, 0

        all_applications = await self._ensure_applications_exist(paths_to_update, project)
        await self._update_all_applications(all_applications, paths_to_update)
        await self.update_log_files(paths_to_update, all_applications)
        next_status = await self._update_high_watermark(paths_to_update, project, indexing_job)
        return next_status, len(paths_to_update)

    async def _scan_and_update_db(self):
        for project in await Project.all():
            indexing_job = IndexingJob(
                records_processed=0,  # start with zero
                end_time=None,
                status=IndexingJobStatus.RUNNING,
            )
            await indexing_job.save()

            # TODO -- add error catching
            status, num_files = await self._scan_and_update_db_for_project(project, indexing_job)
            logger.info(f"Scanned: {num_files} files with status stored at ID={status.id}")

            indexing_job.records_processed = num_files
            indexing_job.end_time = datetime.datetime.utcnow()
            # TODO -- handle failure
            indexing_job.status = IndexingJobStatus.SUCCESS
            indexing_job.index_status = status
            await indexing_job.save()

    async def update(self):
        await self._update_projects()
        await self._scan_and_update_db()

    async def lifespan(self, app: FastAPI):
        if not os.path.exists(dirname := os.path.dirname(settings.DB_PATH)):
            os.mkdir(dirname)
        async with RegisterTortoise(app, config=settings.TORTOISE_ORM, add_exception_handlers=True):
            yield

    async def list_projects(self, request: fastapi.Request) -> Sequence[schema.Project]:
        project_query = await Project.all()
        out = []
        for project in project_query:
            latest_logfile = (
                await LogFile.filter(application__project=project).order_by("-created_at").first()
            )
            out.append(
                schema.Project(
                    name=project.name,
                    id=project.name,
                    uri=project.uri if project.uri is not None else "TODO",
                    last_written=latest_logfile.created_at
                    if latest_logfile is not None
                    else project.created_at,
                    created=project.created_at,
                    num_apps=await Application.filter(project=project).count(),
                )
            )
        return out

    async def list_apps(
        self,
        request: fastapi.Request,
        project_id: str,
        partition_key: Optional[str],
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[schema.ApplicationSummary]:
        # TODO -- distinctify between project name and project ID
        # Currently they're the same in the UI but we'll want to have them decoupled
        app_query = (
            Application.filter(project__name=project_id)
            if partition_key is None
            else Application.filter(project__name=project_id, partition_key=partition_key)
        )

        applications = (
            # Sentinel value for partition_key is __none__ -- passing it in required makes querying easier
            await app_query.annotate(
                latest_logfile_created_at=functions.Max("log_files__created_at"),
                logfile_count=functions.Max("log_files__max_sequence_id"),
            )
            .order_by("created_at")
            .offset(offset)
            .limit(limit)
            .prefetch_related("log_files", "project")
        )
        out = []
        for application in applications:
            last_written = (
                datetime.datetime.fromisoformat(application.latest_logfile_created_at)
                if (application.latest_logfile_created_at is not None)
                else application.created_at
            )
            out.append(
                schema.ApplicationSummary(
                    app_id=application.name,
                    partition_key=application.partition_key,
                    first_written=application.created_at,
                    last_written=last_written,
                    num_steps=application.logfile_count,
                    tags={},
                )
            )
        return out

    async def get_application_logs(
        self, request: fastapi.Request, project_id: str, app_id: str, partition_key: str
    ) -> ApplicationLogs:
        # TODO -- handle partition keys
        query = (
            Application.filter(name=app_id, project__name=project_id)
            if partition_key is None
            else Application.filter(
                name=app_id, project__name=project_id, partition_key=partition_key
            )
        )
        applications = await query.all()
        application = applications[0]
        application_logs = await LogFile.filter(application__id=application.id).order_by(
            "-created_at"
        )
        async with self._session.create_client("s3") as client:
            # Get all the files
            files = await utils.gather_with_concurrency(
                1,
                _query_s3_file(self._bucket, application.graph_file_pointer, client),
                # _query_s3_files(self.bucket, application.metadata_file_pointer, client),
                *itertools.chain(
                    _query_s3_file(self._bucket, log_file.s3_path, client)
                    for log_file in application_logs
                ),
            )
        graph_data = ApplicationModel.parse_raw(files[0])
        # TODO -- deal with what happens if the application is None
        # TODO -- handle metadata
        # metadata = ApplicationMetadataModel.parse_raw(files[1])
        steps = Step.from_logs(list(itertools.chain(*[f.splitlines() for f in files[1:]])))

        return ApplicationLogs(
            children=[],
            steps=steps,
            # TODO -- get this in
            parent_pointer=None,
            spawning_parent_pointer=None,
            application=graph_data,
        )

    async def indexing_jobs(
        self, offset: int = 0, limit: int = 100, filter_empty: bool = True
    ) -> Sequence[schema.IndexingJob]:
        indexing_jobs_query = (
            IndexingJob.all().order_by("-start_time").prefetch_related("index_status__project")
        )

        # Apply filter conditionally
        if filter_empty:
            indexing_jobs_query = indexing_jobs_query.filter(records_processed__gt=0)
        indexing_jobs = await indexing_jobs_query.offset(offset).limit(limit)
        out = []
        for indexing_job in indexing_jobs:
            out.append(
                schema.IndexingJob(
                    id=indexing_job.id,
                    start_time=indexing_job.start_time,
                    end_time=indexing_job.end_time,
                    status=indexing_job.status,
                    records_processed=indexing_job.records_processed,
                    metadata={
                        "project": indexing_job.index_status.project.name
                        if indexing_job.index_status
                        else "unknown",
                        "s3_highwatermark": indexing_job.index_status.s3_highwatermark
                        if indexing_job.index_status
                        else "unknown",
                    },
                )
            )
        return out


if __name__ == "__main__":
    os.environ["BURR_LOAD_SNAPSHOT_ON_START"] = "True"
    import asyncio

    be = SQLiteS3Backend.from_settings(S3Settings())
    # coro = be.snapshot()  # save to s3
    # asyncio.run(coro)
    coro = be.load_snapshot()  # load from s3
    asyncio.run(coro)
