=====
Hooks
=====

.. _hooks:

Burr has a system of lifecycle adapters (adapted from the similar `Hamilton <https://github.com/dagworks-inc/hamilton>`_ concept), which allow you to run tooling before and after
various places in a node's execution. For instance, you could:

1. Log every step as a trace in datadog
2. Add a time-delay to your steps to allow for rendering
3. Add a print statement to every step to see what happened (E.G. implement the printline in cowsay above)
4. Synchronize state/updates to an external database
5. Put results on a queue to feed to some monitoring system

Note some of the above are yet to be implemented.

To implement hooks, you subclass any number of the :ref:`available lifecycle hooks <hooksref>`.
These have synchronous and asynchronous versions, and your hook can subclass as many as you want
(as long as it doesn't do both the synchronous and asynchronous versions of the same hook).

To use them, you pass them into the :py:class:`ApplicationBuilder <burr.core.application.ApplicationBuilder>` as a ``*args`` list of hooks. For instance,
a hook that prints out the nodes name during execution looks like this.
We implement the pre/post run step hooks.

.. code-block:: python

    class PrintLnHook(PostRunStepHook, PreRunStepHook):
        def pre_run_step(self, *, state: "State", action: "Action", **future_kwargs: Any):
            print(f"Starting action: {action.node.name}")

        def post_run_step(
            self,
            *,
            state: "State",
            action: "Action",
            result: Optional[dict],
            sequence_id: int,
            exception: Exception,
            **future_kwargs: Any,
        ):
            print(f"Finishing action: {action.node.name}")

To include this in the application, you pass it into the :py:meth:`with_hooks <burr.core.application.ApplicationBuilder.with_hooks>` method.

.. code-block:: python

    app = (
        ApplicationBuilder()
        .with_hooks(PrintLnHook())
        ...
        .build())

.. note::

    There are synchronous and asynchronous hooks. Synchronous hooks will be called with both synchronous and asynchronous run methods
    (all of ``step``, ``astep``, ``iterate``, ``aiterate``, ``run``, and ``arun``), whereas synchronous hooks will only be called with
    the asynchronous methods (``astep``, ``aiterate``, ``arun``).

.. warning::
    Hook order is currently undefined -- they happen to be called now in the order in which they are defined. We will likely
    alter them to be called in the order they are defined (for `pre...`) hooks and in reverse order for `post...` hooks,
    but this is not yet implemented.

Read more about the hook API in the :ref:`hooks section <hooksref>`.
