import abc

from burr.lifecycle import (
    PostApplicationCreateHook,
    PostEndSpanHook,
    PostRunStepHook,
    PreRunStepHook,
    PreStartSpanHook,
)
from burr.lifecycle.base import (
    DoLogAttributeHook,
    PostEndStreamHook,
    PostStreamItemHook,
    PreStartStreamHook,
)


class SyncTrackingClient(
    PostApplicationCreateHook,
    PreRunStepHook,
    PostRunStepHook,
    PreStartSpanHook,
    PostEndSpanHook,
    DoLogAttributeHook,
    PreStartStreamHook,
    PostStreamItemHook,
    PostEndStreamHook,
    abc.ABC,
):
    """Base class for synchronous tracking clients. All tracking clients must implement from this
    TODO -- create an async tracking client"""

    @abc.abstractmethod
    def copy(self):
        pass


TrackingClient = SyncTrackingClient
