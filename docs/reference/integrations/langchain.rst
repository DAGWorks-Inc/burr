---------
Langchain
---------

Burr works out of the box with langchain, as Burr delegates to any python code.

There are multiple examples of Burr leveraging langchain, including:

- `Multi agent collaboration <https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/lcel>`_
- `LCEL + Hamilton together <https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/hamilton>`_

Burr also provides custom ser/deserialization for langchain objects. See the following resources:
1. `Example <https://github.com/DAGWorks-Inc/burr/tree/main/examples/custom-serde>`_
2. :ref:`Custom serialization docs <serde>`
3. `Langchain serialization plugin <https://github.com/DAGWorks-Inc/burr/blob/main/burr/integrations/serde/langchain.py>`_

We are working on adding more builtin support for LCEL (LCELActions), and considering adding burr callbacks for tracing langgraph in the Burr
UI. If you have any suggestions, please let us know.
