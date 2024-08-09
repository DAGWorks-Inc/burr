=======================
Conditions/Transitions
=======================

.. _transitionref:

Conditions represent choices to move between actions -- these are read by the application builder when executing the graph.
Note that these will always be specified in order -- the first condition that evaluates to ``True`` will be the selected action.

.. autoclass:: burr.core.action.Condition
   :special-members: __and__, __or__, __invert__
   :members:

   .. automethod:: __init__
