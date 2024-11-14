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

------------------------------------
Description of different targets
------------------------------------

.. code-block:: bash

    pip install burr

This only installs the framework. Zero other dependencies. All other installs below all install the
framework + some other dependencies.

.. code-block:: bash

    pip install "burr[cli]"

This installs the dependencies to run the burr CLI, i.e. `burr --help`.

.. code-block:: bash

    pip install "burr[developer]"

This installs all the dependencies for developing locally.


.. code-block:: bash

    pip install "burr[documentation]"

This installs the dependencies to build the documentation.

.. code-block:: bash

    pip install "burr[examples]"

This installs the dependencies for the examples.


.. code-block:: bash

    pip install "burr[graphviz]"

This installs the dependencies to visualize the graph.

.. code-block:: bash

    pip install "burr[hamilton]"

This installs the dependencies for Hamilton.

.. code-block:: bash

    pip install "burr[haystack]"

This installs the dependencies for Haystack.

.. code-block:: bash

    pip install "burr[learn]"

This installs the dependencies for the UI, CLI, and running demos. It is equivalent to `start` below.

.. code-block:: bash

    pip install "burr[opentelemetry]"

This installs the dependencies for using OpenTelemetry with Burr.

.. code-block:: bash

    pip install "burr[postgresql]"

This installs the dependencies for PostgreSQL.

.. code-block:: bash

    pip install "burr[pydantic]"

This installs the dependencies for Pydantic.

.. code-block:: bash

    pip install "burr[redis]"

This installs the dependencies for Redis.

.. code-block:: bash

    pip install "burr[start]"

This installs the dependencies for the UI, CLI, and running demos. It is equivalent to `learn` above.

.. code-block:: bash

    pip install "burr[streamlit]"

This installs the dependencies for Streamlit.

.. code-block:: bash

    pip install "burr[tests]"

This installs the dependencies for running unit tests.

.. code-block:: bash

    pip install "burr[tracking]"

This installs the client and server dependencies for tracking and running the UI from tracking that is on a filesystem.

.. code-block:: bash

    pip install "burr[tracking-client]"

This installs the client dependencies for tracking to a filesystem.

.. code-block:: bash

    pip install "burr[tracking-client-s3]"

This installs the client dependencies for tracking to S3.

.. code-block:: bash

    pip install "burr[tracking-server-s3]"

This installs the server dependencies to run the UI and load tracking that was sent to S3.

.. code-block:: bash

    pip install "burr[tracking-server]"

This installs the server dependencies for running the UI off a filesystem.
