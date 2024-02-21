import datetime
from typing import Dict, Optional, Sequence

import pydantic

from burr.tracking.common.models import ApplicationModel, BeginEntryModel, EndEntryModel


class Project(pydantic.BaseModel):
    name: str
    id: str  # defaults to name for local, not for remote
    uri: str  # TODO -- figure out what
    last_written: datetime.datetime
    created: datetime.datetime
    num_apps: int


class ApplicationSummary(pydantic.BaseModel):
    app_id: str
    first_written: datetime.datetime
    last_written: datetime.datetime
    num_steps: int
    tags: Dict[str, str]


class Step(pydantic.BaseModel):
    step_start_log: BeginEntryModel
    step_end_log: Optional[EndEntryModel]
    step_sequence_id: int  # unique id for the step within the application


class ApplicationLogs(pydantic.BaseModel):
    application: ApplicationModel
    steps: Sequence[Step]
