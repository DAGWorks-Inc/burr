====================
Transitions
====================

.. _transitions:

.. note::

    While actions form the steps taken in an `application`, transitions decide which one to do next.
    They make decisions based on state. You can use them to specify which model to call, whether a conversation is
    over, or any other decision that needs to be made based on the current state.

Transitions define explicitly how actions are connected and which action is available next for any given state.
You can think of them as edges in a graph.

They have three main components:
- The ``from`` state
- The ``to`` state
- The ``condition`` that must be met to move from the ``from`` state to the ``to``

----------
Conditions
----------

Conditions have a few APIs, but the most common are the three convenience functions:

.. code-block:: python

    from burr.core import when, expr, default
    with_transitions(
        ("from", "to", when(foo="bar"),  # will evaluate when the state has the variable "foo" set to the value "bar"
        ("from", "to", expr('epochs>100')) # will evaluate to True when epochs is greater than 100
        ("from", "to", default)  # will always evaluate to True
        ("from", "to") # leaving out a third conditions we allow defaults
    )


Conditions are evaluated in the order they are specified, and the first one that evaluates to True will be the transition that is selected
when determining which action to run next. If no condition evaluates to ``True``, the application execution will stop early.

The ``~`` operator will invert a condition. For instance:

.. code-block:: python

    from burr.core import when, expr
    with_transitions(
        ("from", "to", ~when(foo="baz"),  # will evaluate to True when foo != baz
        ("from", "to", ~expr('epochs<=100')) # will evaluate to True when epochs hits 101
    )

All keys present in the condition (E.G. ``foo`` and ``epochs`` above) must be present in the state for the condition to work. It will error otherwise.

.. note::

    The ``default`` condition is a special case, and will always evaluate to ``True``. It is useful for defining a "catch-all" transition
    that will be selected if no other condition is met. If you pass a tuple of length 2 to :py:meth:`with_transitions <burr.core.application.ApplicationBuilder.with_transitions>`, the
    default condition will be used.

See the :ref:`transition docs <transitionref>` for more information on the transition API.
