import importlib
import logging
import os
from contextlib import asynccontextmanager
from importlib.resources import files
from typing import Sequence

from starlette import status

# TODO -- remove this, just for testing
from burr.log_setup import setup_logging
from burr.tracking.server.backend import BackendBase, IndexingBackendMixin, SnapshottingBackendMixin

setup_logging(logging.INFO)

logger = logging.getLogger(__name__)

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi_utils.tasks import repeat_every
    from starlette.templating import Jinja2Templates

    from burr.tracking.server import schema
    from burr.tracking.server.schema import ApplicationLogs, BackendSpec, IndexingJob

    # dynamic importing due to the dashes (which make reading the examples on github easier)
    email_assistant = importlib.import_module("burr.examples.email-assistant.server")
    chatbot = importlib.import_module("burr.examples.multi-modal-chatbot.server")
    streaming_chatbot = importlib.import_module("burr.examples.streaming-fastapi.server")

except ImportError as e:
    raise e
    # require_plugin(
    #     e,
    #     [
    #         "click",
    #         "fastapi",
    #         "uvicorn",
    #         "pydantic",
    #         "fastapi-pagination",
    #         "aiofiles",
    #         "requests",
    #         "jinja2",
    #     ],
    #     "tracking",
    # )

SERVE_STATIC = os.getenv("BURR_SERVE_STATIC", "true").lower() == "true"

SENTINEL_PARTITION_KEY = "__none__"

backend = BackendBase.create_from_env()


# if it is an indexing backend we want to expose a few endpoints


# TODO -- add a health check for intialization


async def sync_index():
    if app_spec.indexing:
        logger.info("Updating backend index...")
        await backend.update()
        logger.info("Updated backend index...")


async def download_snapshot():
    if app_spec.snapshotting:
        logger.info("Downloading snapshot of DB for backend to use")
        await backend.load_snapshot()
        logger.info("Downloaded snapshot of DB for backend to use")


first_snapshot = True


async def save_snapshot():
    # is_first is due to the weirdness of the repeat_every decorator
    # It has to be called but we don't want this to run every time
    # So we just skip the first
    global first_snapshot
    if first_snapshot:
        first_snapshot = False
        return
    if app_spec.snapshotting:
        logger.info("Saving snapshot of DB for recovery")
        await backend.snapshot()
        logger.info("Saved snapshot of DB for recovery")


initialized = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Download if it does it
    # For now we do this before the lifespan
    await download_snapshot()
    # No yield from allowed
    await backend.lifespan(app).__anext__()
    await sync_index()  # this will trigger the repeat every N seconds
    await save_snapshot()  # this will trigger the repeat every N seconds
    global initialized
    initialized = True
    yield
    await backend.lifespan(app).__anext__()


app = FastAPI(lifespan=lifespan)


@app.get("/ready")
def is_ready():
    if not initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Backend is not ready yet."
        )
    return {"ready": True}


@app.get("/api/v0/metadata/app_spec", response_model=BackendSpec)
def get_app_spec():
    is_indexing_backend = isinstance(backend, IndexingBackendMixin)
    is_snapshotting_backend = isinstance(backend, SnapshottingBackendMixin)
    supports_demos = backend.supports_demos()
    return BackendSpec(
        indexing=is_indexing_backend,
        snapshotting=is_snapshotting_backend,
        supports_demos=supports_demos,
    )


app_spec = get_app_spec()

logger = logging.getLogger(__name__)

if app_spec.indexing:
    update_interval = backend.update_interval_milliseconds() / 1000 if app_spec.indexing else None
    sync_index = repeat_every(
        seconds=backend.update_interval_milliseconds() / 1000,
        wait_first=True,
        logger=logger,
    )(sync_index)

if app_spec.snapshotting:
    snapshot_interval = (
        backend.snapshot_interval_milliseconds() / 1000 if app_spec.snapshotting else None
    )
    save_snapshot = repeat_every(
        seconds=backend.snapshot_interval_milliseconds() / 1000,
        wait_first=True,
        logger=logger,
    )(save_snapshot)


@app.get("/api/v0/projects", response_model=Sequence[schema.Project])
async def get_projects(request: Request) -> Sequence[schema.Project]:
    """Gets all projects visible by the user.

    :param request: FastAPI request
    :return:  a list of projects visible by the user
    """
    return await backend.list_projects(request)


@app.get(
    "/api/v0/{project_id}/{partition_key}/apps", response_model=Sequence[schema.ApplicationSummary]
)
async def get_apps(
    request: Request, project_id: str, partition_key: str
) -> Sequence[schema.ApplicationSummary]:
    """Gets all apps visible by the user

    :param request: FastAPI request
    :param project_id: project name
    :return: a list of projects visible by the user
    """
    if partition_key == SENTINEL_PARTITION_KEY:
        partition_key = None
    return await backend.list_apps(request, project_id, partition_key=partition_key)


@app.get("/api/v0/{project_id}/{app_id}/{partition_key}/apps")
async def get_application_logs(
    request: Request, project_id: str, app_id: str, partition_key: str
) -> ApplicationLogs:
    """Lists steps for a given App.
    TODO: add streaming capabilities for bi-directional communication
    TODO: add pagination for quicker loading

    :param request: FastAPI
    :param project_id: ID of the project
    :param app_id: ID of the assIndociated application
    :return: A list of steps with all associated step data
    """
    if partition_key == SENTINEL_PARTITION_KEY:
        partition_key = None
    return await backend.get_application_logs(
        request, project_id=project_id, app_id=app_id, partition_key=partition_key
    )


@app.get("/api/v0/ready")
async def ready() -> bool:
    return True


@app.get("/api/v0/indexing_jobs", response_model=Sequence[IndexingJob])
async def get_indexing_jobs(
    offset: int = 0, limit: int = 100, filter_empty: bool = True
) -> Sequence[IndexingJob]:
    if not app_spec.indexing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This backend does not support indexing jobs.",
        )
    return await backend.indexing_jobs(offset=offset, limit=limit, filter_empty=filter_empty)


@app.get("/api/v0/version")
async def version() -> dict:
    """Returns the burr version"""
    import pkg_resources

    try:
        version = pkg_resources.get_distribution("burr").version
    except pkg_resources.DistributionNotFound:
        version = "unknown"
    return {"version": version}


# Examples -- todo -- put them behind `if` statements
app.include_router(chatbot.router, prefix="/api/v0/chatbot")
app.include_router(email_assistant.router, prefix="/api/v0/email_assistant")
app.include_router(streaming_chatbot.router, prefix="/api/v0/streaming_chatbot")

if SERVE_STATIC:
    BASE_ASSET_DIRECTORY = str(files("burr").joinpath("tracking/server/build"))

    templates = Jinja2Templates(directory=BASE_ASSET_DIRECTORY)
    app.mount(
        "/static", StaticFiles(directory=os.path.join(BASE_ASSET_DIRECTORY, "static")), "/static"
    )
    # public assets in create react app don't get put under build/static, we need to route them over
    app.mount("/public", StaticFiles(directory=BASE_ASSET_DIRECTORY, html=True), "/public")

    @app.get("/{rest_of_path:path}")
    async def react_app(req: Request, rest_of_path: str):
        """Quick trick to server the react app
        Thanks to https://github.com/hop-along-polly/fastapi-webapp-react for the example/demo
        """
        return templates.TemplateResponse("index.html", {"request": req})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Default to 8000 if no PORT environment variable is set
    uvicorn.run(app, host="0.0.0.0", port=port)
