import datetime
from typing import Dict, List, Optional

import pydantic

from burr.tracking.common.models import (
    ApplicationModel,
    BeginEntryModel,
    BeginSpanModel,
    EndEntryModel,
    EndSpanModel,
)


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


class Span(pydantic.BaseModel):
    """Represents a span. These have action sequence IDs associated with
    them to put them in order."""

    begin_entry: BeginSpanModel
    end_entry: Optional[EndSpanModel]


class Step(pydantic.BaseModel):
    """Log of  astep -- has a start and an end."""

    step_start_log: BeginEntryModel
    step_end_log: Optional[EndEntryModel]
    spans: List[Span]


class ApplicationLogs(pydantic.BaseModel):
    """Application logs are purely flat --
    we will likely be rethinking this but for now this provides for easy parsing."""

    application: ApplicationModel
    steps: List[Step]
