import dataclasses
from typing import Optional


# This contains commmon types
# Currently the types are a little closer to the logic than we'd like
# We'll want to break them out into interfaces and put more here eventually
# This will help avoid the ugly if TYPE_CHECKING imports;
@dataclasses.dataclass
class ParentPointer:
    app_id: str
    partition_key: Optional[str]
    sequence_id: Optional[int]
