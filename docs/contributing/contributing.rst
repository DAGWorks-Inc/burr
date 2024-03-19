============
Contributing
============

Please read the `code of conduct <https://github.com/dagworks-inc/burr/tree/main/CODE_OF_CONDUCT.md>`_
prior to contributing. Then follow these guidelines:

#. Create a fork of the repository.
#. Ensure all tests pass
#. Make a PR to the main repository
#. Ping one of the maintainers to review your PR (best way to reach us is via the `slack community <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg>`_)

-----------------------
Contribution guidelines
-----------------------

Please:

#. Keep your commits modular
#. Add descriptive commit messages
#. Attach a PR to an issue if applicable
#. Ensure all new features have tests
#. Add documentation for new features


---------------
Developer notes
---------------

CLI
---

Burr comes with a `cli` that is both user/developer facing.

**this is required in order to publish, do not do so otherwise**

This will be turned into a `Makefile`, but for now we have a set of commands in `pyproject.toml` that are used to
publish, etc...

To run the just the server for development:

.. code-block:: bash

    $ burr --dev-mode --no-open # will run the server on port 7241

To publish -- this will build the FE + publish the BE to the ``pypi`` prod instance. Note you have to have ``pypi`` credentials to do this:

.. code-block:: bash

    $ burr-admin-publish --prod

To generate the demo data (if you make a change to the schema, ideally forward-compatible):

.. code-block:: bash

    $ burr-admin-generate-demo-data

Not part of the CLI (yet), but running just the UI is simple:

.. code-block:: bash

        $ cd burr/ui
        $ npm run start

Package data
------------

Several static assets are included in the python package so we can run the UI. Namely:

1. The `examples` directory is symlinked from ``burr/examples`` to allow for package-style imports
2. The `build/` directory is symlinked from ``burr/tracking/server`` to allow for static assets referred to by the server to be included in the package. Note that this does not get committed -- this requires use of the CLI above.
