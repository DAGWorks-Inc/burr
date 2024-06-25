============
Applications
============

Use this to build and manage a state Machine. You should only ever instantiate the ``ApplicationBuilder`` class,
and not the ``Application`` class directly.


.. autoclass:: burr.core.application.ApplicationBuilder
   :members:

.. _applicationref:

.. autoclass:: burr.core.application.Application
   :members:

   .. automethod:: __init__

.. autoclass:: burr.core.application.ApplicationGraph
   :members:

.. autoclass:: burr.core.application.ApplicationContext
   :members:

==========
Graph APIs
==========

You can, optionally, use the graph API along with the :py:meth:`burr.core.application.ApplicationBuilder.with_graph`
method. While this is a little more verbose, it helps decouple application logic from graph logic, and is useful in a host
of situations.

The ``GraphBuilder`` class is used to build a graph, and the ``Graph`` class can be passed to the application builder.

.. autoclass:: burr.core.graph.GraphBuilder
   :members:

.. autoclass:: burr.core.graph.Graph
   :members:
