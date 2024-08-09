=====
Setup
=====

These instructions will be assuming use of `pip <https://pip.pypa.io/en/stable/>`_ and `virtualenv <https://virtualenv.pypa.io/>`_.
Replace with your package manager of choice if you prefer.

----------
Clone/fork
----------

To get started, create a fork of Burr on the github UI, and clone it to your local machine.

.. code-block:: bash

    git clone https://github.com/<your_space>/burr.git


----------
Installing
----------

Next you'll want to ``cd`` into the directory and install
``burr`` in developer mode:

.. code-block:: bash

    cd burr
    pip install -e ".[developer]"

This will install all potential dependencies. Burr will work with ``python >=3.9``.

------------------
Linting/Pre-Commit
------------------

Burr has pre-commit hooks enabled. This comes with the ``developer`` extras.
You can always run the pre-commit hooks manually (on all files). Do this
if it somehow wasn't configured and its in a bad state.

.. code-block:: bash

    pre-commit run --all

For the UI, we leverage husky and lint-staged to run the pre-commit hooks on the client side.
This actually runs pre-commits for the whole repository, so you can run through husky if you want.

You can also run the pre-commit hooks for the UI manually:

.. code-block:: bash

    npm run lint:fix
    npm run format:fix

from within the ``telemetry/ui`` directory.
