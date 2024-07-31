from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "project" (
    "created_at" TIMESTAMP NOT NULL,
    "indexed_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "uri" VARCHAR(255)
) /* Static model representing a project */;
CREATE INDEX IF NOT EXISTS "idx_project_name_4d952a" ON "project" ("name");
CREATE TABLE IF NOT EXISTS "application" (
    "created_at" TIMESTAMP NOT NULL,
    "indexed_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "partition_key" VARCHAR(255) NOT NULL,
    "graph_file_pointer" VARCHAR(255),
    "metadata_file_pointer" VARCHAR(255),
    "fork_parent_id" INT REFERENCES "application" ("id") ON DELETE CASCADE,
    "project_id" INT NOT NULL REFERENCES "project" ("id") ON DELETE CASCADE,
    "spawning_parent_id" INT REFERENCES "application" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_application_name_488894" UNIQUE ("name", "partition_key")
);
CREATE INDEX IF NOT EXISTS "idx_application_name_18706d" ON "application" ("name");
CREATE INDEX IF NOT EXISTS "idx_application_partiti_d302c8" ON "application" ("partition_key");
CREATE INDEX IF NOT EXISTS "idx_application_project_13a4e1" ON "application" ("project_id");
CREATE TABLE IF NOT EXISTS "indexstatus" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "s3_highwatermark" VARCHAR(1023) NOT NULL,
    "captured_time" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "project_id" INT NOT NULL REFERENCES "project" ("id") ON DELETE CASCADE
) /* Status to index. These are per-project and the latest is chosen */;
CREATE INDEX IF NOT EXISTS "idx_indexstatus_capture_d2163c" ON "indexstatus" ("captured_time");
CREATE INDEX IF NOT EXISTS "idx_indexstatus_project_52e6eb" ON "indexstatus" ("project_id");
CREATE TABLE IF NOT EXISTS "indexingjob" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "start_time" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "records_processed" INT NOT NULL,
    "end_time" TIMESTAMP,
    "status" VARCHAR(7) NOT NULL  /* SUCCESS: SUCCESS\nFAILURE: FAILURE\nRUNNING: RUNNING */,
    "index_status_id" INT REFERENCES "indexstatus" ("id") ON DELETE CASCADE
) /* Job for indexing data in s3. Records only if there's something to index */;
CREATE TABLE IF NOT EXISTS "logfile" (
    "created_at" TIMESTAMP NOT NULL,
    "indexed_at" TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "s3_path" VARCHAR(1024) NOT NULL,
    "tracker_id" VARCHAR(255) NOT NULL,
    "min_sequence_id" INT NOT NULL,
    "max_sequence_id" INT NOT NULL,
    "application_id" INT NOT NULL REFERENCES "application" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_logfile_applica_9633be" ON "logfile" ("application_id");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
