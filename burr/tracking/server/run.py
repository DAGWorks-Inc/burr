from typing import Sequence

from fastapi import FastAPI, Request

from burr.tracking.server import backend, schema
from burr.tracking.server.schema import ApplicationLogs

app = FastAPI()

backend = backend.LocalBackend()


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
