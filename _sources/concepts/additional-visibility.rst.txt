=====================
Additional Visibility
=====================

Burr comes with the ability to see inside your actions. This is a very pluggable framework
that comes with the default tracking client.


-------
Tracing
-------

Burr comes with a tracing capability to see recursive spans inside an action. This is similar to
the `OpenTelemetry <https://opentelemetry.io/>`_ sdk, although it is simplified significantly.

To add the tracing capability, the action first has to declare a ``__tracer`` input. This is a
an object that instantiates spans and tracks state.

Then, using the `__tracer` as a callable, you can instantiate spans and track state.

For the function-based API, this would look as follows:

.. code-block:: python

    from burr.visibility import TracingFactory
    from burr.core import action

    @action(reads=['input_var'], writes=['output_var'])
    def my_action(state: State, __tracer: TracingFactory) -> Tuple[dict, State]:
        with __tracer('process_data'):
            initial_data = _process_data(state['input_var'])
            with __tracer('validate_data'):
                _validate(initial_data)
        with __tracer('transform_data', dependencies=['process_data']):
            transformed_data = _transform(initial_data)
        return {'output_var': transformed_data}, state.update({'output_var': transformed_data})


This would create the following traces:

#. ``process_data``
#. ``validate_data`` as a child of ``process_data``
#. ``transform_data`` as a causal dependent of ``process_data``

Dependencies are used to express [dag](-style structures of spans within actions. This is useful for gaining visibility into the internal structure
of an action, but is likely best used with integrations with micro-orchestration systems for implementating actions, such as Hamilton or Lanchain.
This maps to the `span link <https://opentelemetry.io/docs/concepts/signals/traces/#span-links>`_ concept in OpenTelemetry.

Note that, on the surface, this doesn't actually *do* anything. It has to be paired with the appropriate hooks.
These just function as callbacks (on enter/exit). The :py:class:`LocalTrackingClient <burr.tracking.LocalTrackingClient>`, used by the
:ref:`tracking <tracking>` feature forms one of these hooks, but we will be adding more, including:

1. An OpenTelemetry client
2. A DataDog client

.. note::

    The class-based API can leverage this by declaring ``inputs`` as ``__tracer`` and then using the ``__tracer`` inside the ``run`` method.

------------
Observations
------------

(This is a work in progress, and is not complete)

You can make observations on the state by calling out to the `log_artifact` method on the `__tracer` context manager.
For instance:

.. code-block:: python

    from burr.visibility import TracingFactory, ArtifactLogger
    from burr.core import action

    @action(reads=['input_var'], writes=['output_var'])
    def my_action(
        state: State,
        __tracer: TracingFactory,
        __logger: ArtifactLogger
        ) -> Tuple[dict, State]:
        with __tracer('process_data'):
            initial_data = _process_data(state['input_var'])
            with __tracer('validate_data'):
                validation_results = _validate(initial_data)
                t.log_artifact(validation_results=validation_results)
        with __tracer('transform_data', dependencies=['process_data'])
            transformed_data = _transform(initial_data)
            __logger.log_artifact(transformed_data_size=len(transformed_data))

        return {'output_var': transformed_data}, state.update({'output_var': transformed_data})

The output can be any "json-dumpable" object (or pydantic model). This will be stored along with the span and can be used for debugging or analysis.

You can read more in the :ref:`reference documentation <visibility>`.
