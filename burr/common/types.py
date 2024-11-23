import abc
import dataclasses
from typing import Any, Optional

try:
    from typing import Self
except ImportError:
    Self = Any


# This contains common types
# Currently the types are a little closer to the logic than we'd like
# We'll want to break them out into interfaces and put more here eventually
# This will help avoid the ugly if TYPE_CHECKING imports;
@dataclasses.dataclass
class ParentPointer:
    app_id: str
    partition_key: Optional[str]
    sequence_id: Optional[int]


class BaseCopyable(abc.ABC):
    """Interface for copying objects. This is used internally."""

    @abc.abstractmethod
    def copy(self) -> "Self":
        pass
