=================
Lifecycle API
=================


These are the available lifecycle hooks for Burr. Implement these classes
and add instances to the application builder to customize your state machines's execution.

.. _hooksref:
.. autoclass:: burr.lifecycle.base.PreRunStepHook
   :members:

.. autoclass:: burr.lifecycle.base.PreRunStepHookAsync
   :members:

.. autoclass:: burr.lifecycle.base.PostRunStepHook
   :members:

.. autoclass:: burr.lifecycle.base.PostRunStepHookAsync
    :members:

.. autoclass:: burr.lifecycle.base.PostApplicationCreateHook
    :members:

These hooks are available for you to use:

.. autoclass:: burr.lifecycle.default.StateAndResultsFullLogger

   .. automethod:: __init__

.. autoclass:: burr.lifecycle.default.SlowDownHook

    .. automethod:: __init__
