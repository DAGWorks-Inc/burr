==========
Developing
==========

-------------
Python Module
-------------

The python module is located in the ``burr/`` directory. Tests are located in the
``tests/`` directory. To run the tests, use the following command:

.. code-block:: bash

    python -m pytest tests/


---------------
Tracking server
---------------

The tracking server is located inside the python package. To run the server, you can use the utility cli:

.. code-block:: bash

    BURR_SERVE_STATIC=false burr-admin-server --no-open --dev-mode

This will start the server on port 7241. Note that this is just a python wrapper -- this also captures stdout.
We will be fixing this, but ff you want to run it directly (which is best for debugging), you'll want to
run it with uvicorn:

.. code-block:: bash

    BURR_SERVE_STATIC=false uvicorn burr.tracking.server.run:app --port 7241 --reload

We disable serving static files as we want to be able to develop simultaneously with the UI and
npm's reloading capabilities do not work with the static python server.

-----------
Tracking UI
-----------

The tracking UI lives within ``telemetry/ui`` To run the tracking UI, you will need to have npm installed.
Then, you can run the following commands:

.. code-block:: bash

    $ cd telemetry/ui
    $ npm install
    $ npm run start

This will start the UI on port 3000. You can then navigate to ``http://localhost:3000`` to see the UI.
It currently assumes that the tracking server is running on port 7241. The proxy is set up in the
``package.json`` file.

Note that if you want to just develop off the server you'll first have to build the UI and symlink the
``tracking/server/build`` directory to the ``telemetry/ui/build`` directory. We have this structure to
enable easy inclusion of package data in ``pyproject.toml``.

You can do this with the following command:

.. code-block:: bash

    $ burr-admin-build-ui

-------------
Documentation
-------------

The documentation is located in the ``docs/`` directory. To build and serve the documentation,
you can use the following sphinx command:

.. code-block:: bash

    $ sphinx-autobuild -b dirhtml -W -E -T  --watch docs/ -a docs /tmp/mydocs

This will start the server on port 8000. You can then navigate to ``http://localhost:8000`` to see the documentation.
Heed any warnings and fix them!
