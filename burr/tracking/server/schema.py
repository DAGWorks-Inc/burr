import collections
import datetime
from typing import Any, Dict, List, Optional

import pydantic
from pydantic import fields

from burr.tracking.common.models import (
    ApplicationModel,
    AttributeModel,
    BeginEntryModel,
    BeginSpanModel,
    ChildApplicationModel,
    EndEntryModel,
    EndSpanModel,
    PointerModel,
)
from burr.tracking.utils import safe_json_load


class Project(pydantic.BaseModel):
    name: str
    id: str  # defaults to name for local, not for remote
    last_written: datetime.datetime
    created: datetime.datetime
    num_apps: int
    uri: str


class ApplicationSummary(pydantic.BaseModel):
    app_id: str
    partition_key: Optional[str]
    first_written: datetime.datetime
    last_written: datetime.datetime
    num_steps: int
    tags: Dict[str, str]
    parent_pointer: Optional[PointerModel] = None
    spawning_parent_pointer: Optional[PointerModel] = None


class ApplicationModelWithChildren(pydantic.BaseModel):
    application: ApplicationModel
    children: List[PointerModel]
    type: str = "application_with_children"


class PartialSpan(pydantic.BaseModel):
    begin_entry: Optional[BeginSpanModel] = fields.Field(default_factory=lambda: None)
    end_entry: Optional[EndSpanModel] = fields.Field(default_factory=lambda: None)


class Span(pydantic.BaseModel):
    """Represents a span. These have action sequence IDs associated with
    them to put them in order."""

    begin_entry: BeginSpanModel
    end_entry: Optional[EndSpanModel]


class PartialStep(pydantic.BaseModel):
    step_start_log: Optional[BeginEntryModel] = fields.Field(default_factory=lambda: None)
    step_end_log: Optional[EndEntryModel] = fields.Field(default_factory=lambda: None)
    spans: List[Span] = fields.Field(default_factory=list)


class Step(pydantic.BaseModel):
    """Log of  astep -- has a start and an end."""

    step_start_log: BeginEntryModel
    step_end_log: Optional[EndEntryModel]
    spans: List[Span]
    attributes: List[AttributeModel]

    @staticmethod
    def from_logs(log_lines: List[bytes]) -> List["Step"]:
        steps_by_sequence_id = collections.defaultdict(PartialStep)
        spans_by_id = collections.defaultdict(PartialSpan)
        attributes_by_step: dict[int, List[AttributeModel]] = collections.defaultdict(list)
        for line in log_lines:
            json_line = safe_json_load(line)
            # TODO -- make these into constants
            if json_line["type"] == "begin_entry":
                begin_step = BeginEntryModel.parse_obj(json_line)
                steps_by_sequence_id[begin_step.sequence_id].step_start_log = begin_step
            elif json_line["type"] == "end_entry":
                step_end_log = EndEntryModel.parse_obj(json_line)
                steps_by_sequence_id[step_end_log.sequence_id].step_end_log = step_end_log
            elif json_line["type"] == "begin_span":
                span = BeginSpanModel.parse_obj(json_line)
                spans_by_id[span.span_id] = PartialSpan(
                    begin_entry=span,
                    end_entry=None,
                )
            elif json_line["type"] == "end_span":
                end_span = EndSpanModel.parse_obj(json_line)
                span = spans_by_id[end_span.span_id]
                span.end_entry = end_span
            elif json_line["type"] == "attribute":
                attribute = AttributeModel.parse_obj(json_line)
                attributes_by_step[attribute.action_sequence_id].append(attribute)
        for span in spans_by_id.values():
            sequence_id = (
                span.begin_entry.action_sequence_id
                if span.begin_entry
                else span.end_entry.action_sequence_id
            )
            step = (
                steps_by_sequence_id[sequence_id] if sequence_id in steps_by_sequence_id else None
            )
            if step is not None:
                if span.begin_entry is not None:
                    full_span = Span(
                        begin_entry=span.begin_entry,
                        end_entry=span.end_entry,
                    )
                    step.spans.append(full_span)
        # filter out all the non-null start steps
        return [
            Step(
                step_start_log=value.step_start_log,
                step_end_log=value.step_end_log,
                spans=[Span(**span.dict()) for span in value.spans if span.begin_entry is not None],
                attributes=attributes_by_step[key],
            )
            for key, value in sorted(steps_by_sequence_id.items())
            if value.step_start_log is not None
        ]


class StepWithMinimalData(Step):
    step_start_log: Optional[BeginEntryModel]


class ApplicationLogs(pydantic.BaseModel):
    """Application logs are purely flat --
    we will likely be rethinking this but for now this provides for easy parsing."""

    application: ApplicationModel
    children: List[ChildApplicationModel]
    steps: List[Step]
    parent_pointer: Optional[PointerModel] = None
    spawning_parent_pointer: Optional[PointerModel] = None


class IndexingJob(pydantic.BaseModel):
    """Generic link for indexing job -- can be exposed in 'admin mode' in the UI"""

    id: int
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    status: str
    records_processed: int
    metadata: Dict[str, Any]


class BackendSpec(pydantic.BaseModel):
    """Generic link for indexing job -- can be exposed in 'admin mode' in the UI"""

    indexing: bool
    snapshotting: bool
    supports_demos: bool
