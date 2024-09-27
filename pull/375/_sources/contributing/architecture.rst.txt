============
Architecture
============

Some notes on the design/implementation of Burr:

--------------
Python Package
--------------

Dependencies
------------
A note on dependencies:

- The core Burr library will have zero dependencies. Currently its only dependency in hamilton, but that will be removed in the future.
- Any other extensions (the server, the CLI, etc...) are allowed dependencies -- specify these as install targets in ``pyproject.toml``
- The dependencies/plugins will live alongside the core library, and contain guards to ensure that the right libraries are installed. You can do this with ``burr.integrations.base.require_plugins``

Coding style
------------
We use type hints for function parameters (and in rare cases inline) to aid development but it is not enforced -- use your best judgement

Versioning
----------

We adhere to `sem-var <https://semver.org/>`_ for versioning. We ensure that:

- Every public facing function/class/variable should:
    - have a docstring
    - have type-hints
    - be exposed through the documentation

If it is not exposed through the documentation it is assumed to be private, and thus will
not be subject to sem-var rules.

We currently are not versioning the server or CLI, but are versioning the core library. Note
that it starts at ``0.x``, which means that we are allowed to make a backwards-incompatible change.
We will make every effort not to do so -- and will provide a migration guide/script if we do.
