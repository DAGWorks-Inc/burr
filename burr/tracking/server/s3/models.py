import enum

from tortoise import fields
from tortoise.models import Model


class IndexingJobStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"


class IndexedModel(Model):
    """Base model for all models that are indexed in s3. Contains data on creating/updating"""

    created_at = fields.DatetimeField(null=False)
    indexed_at = fields.DatetimeField(null=True, auto_now_add=True)
    updated_at = fields.DatetimeField(null=False, auto_now=True)

    class Meta:
        abstract = True


class IndexingJob(Model):
    """Job for indexing data in s3. Records only if there's something to index"""

    id = fields.IntField(pk=True)
    start_time = fields.DatetimeField(auto_now_add=True)
    records_processed = fields.IntField()
    end_time = fields.DatetimeField(null=True)
    status = fields.CharEnumField(IndexingJobStatus)
    index_status = fields.ForeignKeyField(
        "models.IndexStatus", related_name="index_status", null=True
    )

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"


class IndexStatus(Model):
    """Status to index. These are per-project and the latest is chosen"""

    id = fields.IntField(pk=True)
    s3_highwatermark = fields.CharField(max_length=1023)
    captured_time = fields.DatetimeField(index=True, auto_now_add=True)
    project = fields.ForeignKeyField("models.Project", related_name="project", index=True)

    def __str__(self):
        return f"{self.project} - {self.captured_time}"


class Project(IndexedModel):
    """Static model representing a project"""

    id = fields.IntField(pk=True)
    name = fields.CharField(index=True, max_length=255, unique=True)
    uri = fields.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name


class Application(IndexedModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(index=True, max_length=255)
    partition_key = fields.CharField(max_length=255, index=True, null=False)
    project = fields.ForeignKeyField("models.Project", related_name="applications", index=True)
    graph_file_pointer = fields.CharField(max_length=255, null=True)
    metadata_file_pointer = fields.CharField(max_length=255, null=True)
    fork_parent = fields.ForeignKeyField("models.Application", related_name="forks", null=True)
    spawning_parent = fields.ForeignKeyField("models.Application", related_name="spawns", null=True)

    class Meta:
        # App name is unique together
        unique_together = (("name", "partition_key"),)

    def graph_file_indexed(self) -> bool:
        return self.graph_file_pointer is not None

    def metadata_file_indexed(self) -> bool:
        return self.metadata_file_pointer is not None


class LogFile(IndexedModel):
    # s3 path is named
    # <tracker_id>-<logfile_sequence>-<min_sequence_id>-<max_sequence_id>.jsonl
    id = fields.IntField(pk=True)
    s3_path = fields.CharField(max_length=1024)
    application = fields.ForeignKeyField(
        "models.Application",
        related_name="log_files",
        index=True,
    )
    tracker_id = fields.CharField(max_length=255)
    min_sequence_id = fields.IntField()
    max_sequence_id = fields.IntField()
