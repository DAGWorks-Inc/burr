.. _tracking:

=============
Tracking Burr
=============

Burr comes with a telemetry system that allows tracking a variety of information for debugging,
both in development and production. Note this is a WIP.

---------------
Tracking Client
---------------

When you use :py:meth:`burr.core.application.ApplicationBuilder.with_tracker`, you add a tracker to Burr.
This is a lifecycle hook that does the following:

#. Logs the static representation of the state machine
#. Logs any information before/after step execution, including
    - The step name
    - The step input
    - The state at time of execution
    - The timestamps

This currently defaults to (and only supports) the :py:class:`burr.tracking.LocalTrackingClient` class, which
writes to a local file system, althoguh we will be making it pluggable in the future.

This will be used with the UI, which can serve out of the specified directory. More coming soon!
