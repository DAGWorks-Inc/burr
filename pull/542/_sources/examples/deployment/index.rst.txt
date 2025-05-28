=============
✈ Deployment
=============

Burr is specifically meant to make getting your product in production easier and faster.
This section covers examples of getting Burr to production, as well as a brief overview of approaches/requirements.

To deploy a Burr application in production, you need to do three things:

1. Place your Burr application in some place you can trigger it. E.g. a web-service, a script, a library, etc.
2. Provision infrastructure to run (1)
3. Monitor your application in production (highly recommended, but not required)

Due to the large number of methods people have for deploying applications, we will not cover all of them here. That said,
we really appreciate contributions! Please `open an issue <https://github.com/DAGWorks-Inc/burr/issues/new?assignees=&labels=&projects=&template=feature_request.md&title=>`_ if there's an example you'd like, and :ref:`contribute back <contributing>` if you
have an example that would add to this guide. We have created a variety of issues with placeholders and link to them in the docs.

.. toctree::
    :maxdepth: 2

    web-server
    infrastructure
    monitoring
