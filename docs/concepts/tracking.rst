.. _tracking:

=============
Tracking Burr
=============

.. note::

    Burr's telemetry system is built in and easy to integrate. It allows you to understand
    the flow of your application, and watch it make decisions in real time. You can run it
    with sample projects by running ``burr`` in the terminal after ``pip install "burr[start]"``.

Burr comes with a telemetry system that allows tracking a variety of information for debugging,
both in development and production.

The data model for tracking is simple:

1. **Projects** are the top-level grouping of data (the first page). This is specified in the constructor for the
   :py:meth:`with_tracker <burr.core.application.ApplicationBuilder.with_tracker>`, as the only required argument.
2. **Applications** get logged to projects. An application would be considered similar to a "trace" in distributed
   tracing systems. This is (optionally) specified as the ``app_id`` argument for the :py:meth:`with_tracker <burr.core.application.ApplicationBuilder.with_tracker>`
   method. A single ``application`` has shared state path across all its steps.
3. **Steps** are the individual steps that are executed in the state machine. The Burr UI will show the state of the
   state machine at the time of the step execution, as well as the input to and results of the step.

.. _trackingclientref:

---------------
Tracking Client
---------------

When you use :py:meth:`with_tracker <burr.core.application.ApplicationBuilder.with_tracker>`, you add a tracker to Burr.
This is a lifecycle hook that does the following:

#. Logs the static representation of the state machine
#. Logs any information before/after step execution, including
    - The step name
    - The step input
    - The state at time of execution
    - The timestamps

This currently defaults to (and only supports) the :py:class:`LocalTrackingClient <burr.tracking.LocalTrackingClient>` class, which
writes to a local file system, although we will be making it pluggable in the future. It will, by default, write to the directory
``~/.burr``.

Debugging via Reloading Prior State
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Because the tracking client writes to the file system, you can reload the state of the state machine at any time. This is
useful for debugging, because you can quickly recreate the issue by running the state machine with the same point in time.

To do so, you'd use the classmethod _load_state()_ on the :py:class:`LocalTrackingClient <burr.tracking.LocalTrackingClient>`.

For example, as you initialize the Burr Application, you'd have some control flow like this:

.. code-block:: python

    from burr.tracking import client

    project_name = "demo:hamilton-multi-agent"
    if app_instance_id:
        initial_state, entry_point = client.LocalTrackingClient.load_state(
            project_name, app_instance_id
        )
        # TODO: any custom logic for re-creating the state if it's some object that needs to be re-instantiated
    else:
        initial_state, entry_point = default_state_and_entry_point()

    app = (
        ApplicationBuilder()
        .with_state(**initial_state)
        .with_entry_point(entry_point)
        # ... etc fill in the rest here
    )

---------------
Tracking Server
---------------

The tracking server (now) is meant for visualizing the state machine and the steps that have been executed. You can
run it with the following command:

.. code-block:: bash

    burr

This will start a server on port 7241, and open up a browser window with the UI for you to explore.
