====================
Transitions
====================

.. _transitions:

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
        ("from", "to", expr('epochs>100')) # will evaluate to True when the state has the variable "foo" set to the value "bar"
        ("from", "to", default)  # will always evaluate to True
    )


Conditions are evaluated in the order they are specified, and the first one that evaluates to True will be the transition that is selected
when determining which action to run next.

Note that if no condition evaluates to ``True``, the application execution will stop early.

See the :ref:`transition docs <transitionref>` for more information on the transition API.
