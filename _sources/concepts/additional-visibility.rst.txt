=====================
Additional Visibility
=====================

.. note::

    Burr comes with the ability to see inside your actions. This is a very pluggable framework
    that comes with the default tracking client, but can also be hooked up to tools such as `OpenTelemetry <https://opentelemetry.io/>`_

-------
Tracing
-------

Burr comes with a tracing capability to see recursive spans inside an action. This is similar to
the `OpenTelemetry <https://opentelemetry.io/>`_ sdk, although it is simplified significantly.

To add the tracing capability, the action first has to declare a ``__tracer`` input. This is a
an object that instantiates spans and tracks state.

Then, using the ``__tracer`` as a callable, you can instantiate spans and track state.

For the function-based API, this would look as follows:

.. code-block:: python

    from burr.visibility import TracingFactory
    from burr.core import action

    @action(reads=['prompt'], writes=['response'])
    def my_action(state: State, __tracer: TracingFactory) -> State:
        with __tracer('create_prompt'):
            modified_prompt = _modify_prompt(state["prompt"])
            with __tracer('check_prompt_safety'):
                if _is_unsafe(modified_prompt):
                    modified_prompt = _fix(modified_prompt)
        with __tracer('call_llm', dependencies=['create_prompt']):
            response = _query(prompt=modified_prompt)
        return state.update({'response': response})


This would create the following traces:

#. ``create_prompt``
#. ``check_prompt_safety`` as a child of ``create_prompt``
#. ``call_llm`` as a causal dependent of ``create_prompt``

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

You can make observations on the state by calling out to the :py:meth:`log_attribute <burr.visibility.ActionSpanTracer.log_attribute>` or :py:meth:`log_attributes <burr.visibility.ActionSpanTracer.log_attributes>` method on the ``__tracer`` context manager
or the root tracer factory.

This allows you to log any arbitrary observations (think token count prompt, whatnot) that may not be part of state/results.

For instance:

.. code-block:: python

    from burr.visibility import TracingFactory
    from burr.core import action

    @action(reads=['prompt'], writes=['response'])
    def my_action(state: State, __tracer: TracingFactory) -> State:
        __tracer.log_attribute(prompt_length=len(state["prompt"]), prompt=state["prompt"])
        with __tracer('create_prompt') as t:
            modified_prompt = _modify_prompt(state["prompt"])
            t.log_attribute(modified_prompt=modified_prompt)
            with __tracer('check_prompt_safety') as t:
                if is_unsafe:=_is_unsafe(modified_prompt):
                    modified_prompt = _fix(modified_prompt)
                t.log_attribute(fixed_prompt=modified_prompt, is_unsafe=is_unsafe)
        with __tracer('call_llm', dependencies=['create_prompt']):
            response = _query(prompt=modified_prompt)
            t.log_attribute(response=response.message, tokens=response.tokens)
        return state.update({'response': response.message})

The above will log quite a few attributes, prompt length, response tokens, etc... The observation can be any serializable object.

Note that we are currently building out the capability to wrap a class and "auto-log" standard attributes.

You can read more in the :ref:`reference documentation <visibility>`.
