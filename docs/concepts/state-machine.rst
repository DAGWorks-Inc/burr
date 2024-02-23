====================
Applications
====================

.. _applications:

Applications form the core representation of the state machine. You build them with the ``ApplicationBuilder``.
Here is the minimum that is required:

1. A ``**kwargs`` of actions passed to ``with_actions(...)``
2. Any relevant transitions (with conditions)
3. An entry point -- this is the first action to execute

This is shown in the example from :ref:`getting started <simpleexample>`

.. code-block:: python

    from burr.core import ApplicationBuilder, default, expr
    app = (
        ApplicationBuilder()
        .with_state(counter=0) # initialize the count to zero
        .with_actions(
            count=count, # add the counter action with the name "counter"
            done=done # add the printer action with the name "printer"
        ).with_transitions(
            ("count", "count", expr("counter < 10")), # Keep counting if the counter is less than 10
            ("count", "done", default) # Otherwise, we're done
        ).with_entrypoint("counter") # we have to start somewhere
        .build()
    )


-------
Running
-------

There are three APIs for executing an application.

``step``/``astep``
------------------

Returns the tuple of the action, the result of that action, and the new state. Call this if you want to run the application step-by-step.

.. code-block:: python

    action, result, state = application.step()

If you're in an async context, you can run `astep` instead:

.. code-block:: python

    action, result, state = await application.astep()


Step can also take in ``inputs`` as a dictionary, which will be passed to the action's run function as keyword arguments.
This is specifically meant for a "human in the loop" scenario, where the action needs to ask for input from a user. In this case,
the control flow is meant to be interrupted to allow for the user to provide input. See :ref:`inputs <inputref>` for more information.

.. code-block:: python

    action, result, state = application.step(inputs={"prompt": input()})

``iterate``/``aiterate``
------------------------

Iterate just runs ``step`` in a row, functioning as a generator:

.. code-block:: python

    for action, result, state in application.iterate(halt_after=["final_action_1", "final_action_2"]):
        print(action.name, result)

You can also run ``aiterate`` in an async context:

.. code-block:: python

    async for action, result, state in application.aiterate():
        print(action.name, result)

In the synchronous context this also has a return value of a tuple of:
1. the action that was specified in `halt_after` or `halt_before`. In the `after` case the action will have already run.
In the `before` case the action will not have run.
2. The result of the action, in the `halt_after` case, else None in the `halt_before` case.
3. The state of the application at the time of halting.

You can access this by looking at the ``value`` variable of the ``StopIteration`` exception that is thrown
at the end of the loop, as is standard for python.
See the function implementation of ``run`` to show how this is done.

In the async context, this does not return anything
(asynchronous generators are not allowed a return value).

.. note::
    You can add inputs to ``iterate``/``aiterate`` by passing in a dictionary of inputs through the ``inputs`` parameter.
    This will only apply to the first action. Actions that are not the first but require inputs are considered undefined behavior.


``run``/``arun``
----------------

Run just calls out to ``iterate`` and returns the final state.

The ``halt_after`` and ``halt_before`` keyword arguments specify when to break out of running the state machine
and return control back. ``halt_after`` will stop after the specified action(s) has run, and ``halt_before`` will stop before the specified action(s) has run.
If multiple are specified, it will stop after the first one encountered, and the return values will be for that action.

.. code-block:: python

    final_state, results = application.run(halt_after=["final_action_1", "final_action_2"])


In the async context, you can run ``arun``:

.. code-block:: python

    final_state = await application.arun(halt_after=["final_action_1", "final_action_2"])

.. note::
    You can add inputs to ``run``/``arun`` in the same way as you can with ``iterate`` -- it will only apply to the first action.

----------
Inspection
----------

You can ask various questions of the state machine using publicly-supported APIs:

- ``application.graph`` will give you a static representation of the state machine with enough information to visualize
- ``application.state`` will give you the current state of the state machine. Note that if you modify it the results will not show up -- state is immutable! Modify the state through actions.

See the :ref:`application docs <applicationref>`
