==========
Installing
==========

Burr itself requires almost no dependencies. Every *extra*/*plugin* is an additional install target.

We recommend you start with installing the ``learn`` target -- this has dependencies necessary to track burr through the UI,
along with a fully built server.

.. code-block:: bash

    pip install "burr[start]"

This will give you tools to visualize, track, and interact with the UI. You can explore the UI (including some sample projects)
simply by running the command ``burr``. Up next we'll write our own application and follow it in the UI.
