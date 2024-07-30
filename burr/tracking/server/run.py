import importlib
import os
from importlib.resources import files
from typing import Optional, Sequence

from burr.integrations.base import require_plugin

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.staticfiles import StaticFiles
    from starlette.templating import Jinja2Templates

    from burr.tracking.server import backend as backend_module
    from burr.tracking.server import schema

    # dynamic importing due to the dashes (which make reading the examples on github easier)
    email_assistant = importlib.import_module("burr.examples.email-assistant.server")
    chatbot = importlib.import_module("burr.examples.multi-modal-chatbot.server")
    streaming_chatbot = importlib.import_module("burr.examples.streaming-fastapi.server")

except ImportError as e:
    require_plugin(
        e,
        [
            "click",
            "fastapi",
            "uvicorn",
            "pydantic",
            "fastapi-pagination",
            "aiofiles",
            "requests",
            "jinja2",
        ],
        "tracking",
    )

app = FastAPI()

SERVE_STATIC = os.getenv("BURR_SERVE_STATIC", "true").lower() == "true"

backend = backend_module.LocalBackend()


@app.get("/api/v0/projects", response_model=Sequence[schema.Project])
async def get_projects(request: Request) -> Sequence[schema.Project]:
    """Gets all projects visible by the user.

    :param request: FastAPI request
    :return:  a list of projects visible by the user
    """
    return await backend.list_projects(request)


@app.get("/api/v0/{project_id}/apps", response_model=Sequence[schema.ApplicationSummary])
async def get_apps(request: Request, project_id: str) -> Sequence[schema.ApplicationSummary]:
    """Gets all apps visible by the user

    :param request: FastAPI request
    :param project_id: project name
    :return: a list of projects visible by the user
    """
    return await backend.list_apps(request, project_id)


@app.get("/api/v0/{project_id}/{app_id}/apps")
async def get_application_logs(
    request: Request, project_id: str, app_id: str
) -> schema.ApplicationLogs:
    """Lists steps for a given App.
    TODO: add streaming capabilities for bi-directional communication
    TODO: add pagination for quicker loading

    :param request: FastAPI
    :param project_id: ID of the project
    :param app_id: ID of the associated application
    :return: A list of steps with all associated step data
    """
    return await backend.get_application_logs(request, project_id=project_id, app_id=app_id)


@app.post("/api/v0/application_ids", response_model=Optional[schema.ApplicationIDs])
def list_app_ids(
    persister_type: str,
    persister_kwargs: dict,
    partition_key: str = None,
    persister_method: str = "constructor",
) -> Optional[schema.ApplicationIDs]:
    """Lists all the app_ids for a given partition key using the provided persister.

    This is meant for debugging use cases.

    :param partition_key: the partition key to list app_ids for
    :param persister_kwargs: the kwargs to pass to the persister class constructor
    :param persister_type: the type of persister to use. This is a fully qualified name, e.g.burr.integrations.persisters.b_redis.RedisPersister
    :param persister_method: the class method to use to create the persister. Defaults to "constructor".
    :return: a list of app_ids
    """
    persister = create_persister(persister_kwargs, persister_method, persister_type)
    app_ids = persister.list_app_ids(partition_key)
    if app_ids is None:
        return None
    return schema.ApplicationIDs(partition_key=partition_key, app_ids=app_ids)


def create_persister(persister_kwargs, persister_method, persister_type):
    """Given the persister type, imports the module and creates the class
    e.g. burr.integrations.persisters.b_redis.RedisPersister
    """
    module_name, class_name = persister_type.rsplit(".", 1)
    module = importlib.import_module(module_name)
    persister_class = getattr(module, class_name)
    if persister_method == "constructor":
        persister = persister_class(**persister_kwargs)
    else:
        persister = getattr(persister_class, persister_method)(**persister_kwargs)
    return persister


@app.post(
    "/api/v0/application_id/{application_id}", response_model=Optional[schema.PersistedStateData]
)
def load_app_step(
    persister_type: str,
    persister_kwargs: dict,
    application_id: str,
    partition_key: str = None,
    sequence_id: int = None,
    persister_method: str = "constructor",
) -> Optional[schema.PersistedStateData]:
    """Loads a persisted value for a given partition_key, application_id [, and sequence_id].

    This is meant for debugging use cases.

    :param persister_type: the type of persister to use. This is a fully qualified name, e.g.burr.integrations.persisters.b_redis.RedisPersister
    :param persister_kwargs: the kwargs to pass to the persister class constructor
    :param application_id: the application_id to load
    :param partition_key: the partition key to list app_ids for
    :param sequence_id: the sequence_id to load. Defaults to None. Gets last one.
    :return: a list of app_ids
    """
    persister = create_persister(persister_kwargs, persister_method, persister_type)
    app_step = persister.load(partition_key, application_id, sequence_id)
    if app_step is None:
        return None
    else:
        return schema.PersistedStateData(
            partition_key=app_step["partition_key"],
            app_id=app_step["app_id"],
            sequence_id=app_step["sequence_id"],
            position=app_step["position"],
            state=app_step["state"].serialize(),
            created_at=app_step["created_at"],
            status=app_step["status"],
        )


@app.get("/api/v0/ready")
async def ready() -> bool:
    return True


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
