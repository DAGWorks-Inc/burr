=============
Installation
=============

Burr itself requires no dependencies. Every *extra*/*plugin* is an additional install target.

We recommend you start with installing the ``start`` target -- this has dependencies necessary to track burr through the UI,
along with a fully built server.

.. code-block:: bash

    pip install "burr[start]"

This will give you tools to visualize, track, and interact with the UI. You can explore the UI (including some sample projects)
simply by running the command ``burr``. Up next we'll write our own application and follow it in the UI.

If you're using poetry, you can't install the ``start`` target directly, due to [this issue](https://github.com/python-poetry/poetry/issues/3369).
Instead, please install manually using the following command:

.. code-block:: bash

    poetry add loguru "burr[tracking-client,tracking-server,streamlit,graphviz,hamilton]"

This is just the kitchen sink for getting started -- remember, burr is dependency-free/pure python!
