-------------------------------------
Provisioning Infrastructure/Deploying
-------------------------------------

Burr is not opinionated about the method of deployment/cloud one uses. Any method that can run python code, or web-service will work
(AWS, vercel, etc...). Note we aim to have more examples here -- see `this issue <https://github.com/DAGWorks-Inc/burr/issues/390>`_ to track!

- `Deploying Burr in an AWS lambda function <https://github.com/DAGWorks-Inc/burr/tree/main/examples/deployment/aws/lambda>`_
- `Deploying Burr using BentoML <https://github.com/DAGWorks-Inc/burr/tree/main/examples/deployment/aws/bentoml>`_


Using BentoML
-------------
[BentoML](https://github.com/bentoml/BentoML) is a specialized tool to package, deploy, and manage AI services.
For example, it allows you to create a REST API for your Burr application with minimal effort.
See the `Burr + BentoML example <https://github.com/DAGWorks-Inc/burr/tree/main/examples/deployment/aws/bentoml>`_ for more information.
