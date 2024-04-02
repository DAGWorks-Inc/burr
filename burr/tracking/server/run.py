import os
from importlib.resources import files
from typing import Sequence

from burr.integrations.base import require_plugin
from burr.tracking.server.examples import chatbot, email_assistant

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.staticfiles import StaticFiles
    from starlette.templating import Jinja2Templates

    from burr.tracking.server import backend as backend_module
    from burr.tracking.server import schema
    from burr.tracking.server.schema import ApplicationLogs
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
async def get_application_logs(request: Request, project_id: str, app_id: str) -> ApplicationLogs:
    """Lists steps for a given App.
    TODO: add streaming capabilities for bi-directional communication
    TODO: add pagination for quicker loading

    :param request: FastAPI
    :param project_id: ID of the project
    :param app_id: ID of the associated application
    :return: A list of steps with all associated step data
    """
    return await backend.get_application_logs(request, project_id=project_id, app_id=app_id)


@app.get("/api/v0/ready")
async def ready() -> bool:
    return True


# Examples -- todo -- put them behind `if` statements
app.include_router(chatbot.router, prefix="/api/v0/chatbot")
app.include_router(email_assistant.router, prefix="/api/v0/email_assistant")
# email_assistant.register(app, "/api/v0/email_assistant")


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
