------------------------
Monitoring in Production
------------------------

Burr's telemetry UI is meant both for debugging and running in production. It can consume `OpenTelemetry traces <https://burr.dagworks.io/reference/integrations/opentelemetry/>`_,
and has a suite of useful capabilities for debugging Burr applications.

It has two (current) implementations:

1. `Local (filesystem) tracking <https://burr.dagworks.io/concepts/tracking/>`_ (default, for debugging or lower-scale production use-cases with a distributed file-system)
2. `S3-based tracking <https://github.com/DAGWorks-Inc/burr/blob/main/burr/tracking/server/s3/README.md>`_ (meant for production use-cases)

Which each come with an implementation of data storage on the server.

To deploy these in production, you can follow the following examples:

1. `Burr + FastAPI + docker <https://github.com/mdrideout/burr-fastapi-docker-compose>`_ by `Matthew Rideout <https://github.com/mdrideout>`_. This contains a sample API + UI + tracking server all bundled in one!
2. `Docker compose + nginx proxy <https://github.com/DAGWorks-Inc/burr/tree/main/examples/email-assistant#running-the-ui-with-email-server-backend-in-a-docker-container>`_ by `Aditha Kaushik <https://github.com/97k>`_ for the email assistant example, demonstrates running the docker image with the tracking server.

We also have a few issues to document deploying Burr's monitoring system in production:

- `deploy on AWS <https://github.com/DAGWorks-Inc/burr/issues/391>`_
- `deploy on GCP <https://github.com/DAGWorks-Inc/burr/issues/392>`_
- `deploy on Azure <https://github.com/DAGWorks-Inc/burr/issues/393>`_
