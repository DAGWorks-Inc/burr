import dataclasses
from typing import Optional


@dataclasses.dataclass
class ParentPointer:
    app_id: str
    partition_key: Optional[str]
    sequence_id: Optional[int]
