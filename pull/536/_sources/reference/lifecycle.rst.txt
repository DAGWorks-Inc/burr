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

.. autoclass:: burr.lifecycle.base.PreStartSpanHook
    :members:

.. autoclass:: burr.lifecycle.base.PreStartSpanHookAsync
    :members:

.. autoclass:: burr.lifecycle.base.PostEndSpanHook
    :members:

.. autoclass:: burr.lifecycle.base.PostEndSpanHookAsync
    :members:

.. autoclass:: burr.lifecycle.base.ExecuteMethod
    :members:

.. autoclass:: burr.lifecycle.base.PreApplicationExecuteCallHook
    :members:

.. autoclass:: burr.lifecycle.base.PreApplicationExecuteCallHookAsync
    :members:

.. autoclass:: burr.lifecycle.base.PostApplicationExecuteCallHook
    :members:

.. autoclass:: burr.lifecycle.base.PostApplicationExecuteCallHookAsync
    :members:

These hooks are available for you to use:

.. autoclass:: burr.lifecycle.default.StateAndResultsFullLogger

   .. automethod:: __init__

.. autoclass:: burr.lifecycle.default.SlowDownHook

    .. automethod:: __init__
