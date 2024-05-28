import abc

from burr.lifecycle import (
    PostApplicationCreateHook,
    PostEndSpanHook,
    PostRunStepHook,
    PreRunStepHook,
    PreStartSpanHook,
)


class SyncTrackingClient(
    PostApplicationCreateHook,
    PreRunStepHook,
    PostRunStepHook,
    PreStartSpanHook,
    PostEndSpanHook,
    abc.ABC,
):
    """Base class for synchronous tracking clients. All tracking clients must implement from this
    TODO -- create an async tracking client"""

    pass


TrackingClient = SyncTrackingClient
