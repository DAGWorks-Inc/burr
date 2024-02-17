====================
Applications
====================

.. _applications:

Applications form the core representation of the state machine. You build them with the ``ApplicationBuilder``.

The ``ApplicationBuilder`` is a class that helps you build an application. Here is the minimum that is required:

1. A ``**kwargs`` of actions passed to ``with_actions(...)``
2. Any relevant transitions (with conditions)
3. An entry point

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

    for action, result, state in application.iterate(until=["final_action_1", "final_action_2"]):
        print(action.name, result)

You can also run ``aiterate`` in an async context:

.. code-block:: python

    async for action, result, state in application.aiterate():
        print(action.name, result)

In the synchronous context this also has a return value of a tuple of:
1. the final state
2. A list of the actions that were run, one for each result

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

The ``until`` variable is a ``or`` gate (E.G. ``any_complete``), although we will be adding an ``and`` gate (E.G. ``all_complete``),
and the ability to run until the state machine naturally executes (``until=None``).

.. code-block:: python

    final_state, results = application.run(until=["final_action_1", "final_action_2"])


In the async context, you can run ``arun``:

.. code-block:: python

    final_state = await application.arun(until=["final_action_1", "final_action_2"])

.. note::
    You can add inputs to ``run``/``arun`` in the same way as you can with ``iterate`` -- it will only apply to the first action.

----------
Inspection
----------

You can ask various questions of the state machine using publicly-supported APIs:

- ``application.graph`` will give you a static reprsentation of the state machine with enough information to visualize
- ``application.state`` will give you the current state of the state machine. Note that if you modify it the results will not show up -- state is immutable!

See the :ref:`application docs <applicationref>`
