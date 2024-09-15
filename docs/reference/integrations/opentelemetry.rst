.. _opentelintegrationref:

--------------
OpenTelemetry
--------------

Burr has two integrations with OpenTelemetry:


1. Burr can log traces to OpenTelemetry
2. Burr can capture any traces logged within an action and log them to OpenTelemetry

See the following resources for more information:

- :ref:`Tracing/OpenTelemetry <opentelref>`
- `Example in the repository <https://github.com/dagworks-inc/burr/tree/main/examples/opentelemetry>`_
- `Blog post <https://blog.dagworks.io/p/9ef2488a-ff8a-4feb-b37f-1d9a781068ac/>`_
- `OpenTelemetry <https://opentelemetry.io/>`_

Reference for the various useful methods:

.. autoclass:: burr.integrations.opentelemetry.OpenTelemetryBridge
    :members:

.. autofunction:: burr.integrations.opentelemetry.init_instruments
