====================
Agents
====================

Burr allows you to create agents that can interact with each other via State.

Multi-Agent Example
--------------------

Here we list the different agent examples we have with Burr.

Divide and Conquer
__________________
A single agent can usually operate effectively using a handful of tools within a single domain, but even using powerful
models like `gpt-4`, it can be less effective at using many tools.

One way to approach complicated tasks is through a "divide-and-conquer" approach: create a "specialized agent" for
each task or domain and route tasks to the correct "expert". This means that each agent can become a sequence of LLM
calls that chooses how to use a specific "tool".

The examples we link to below are inspired by the paper `AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation by Wu, et. al. <https://arxiv.org/abs/2308.08155>`_.
They can be found in `this part of our repository <https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration>`_.

We have two implementations that show case this. One uses LangChain's LCEL, the other uses Hamilton. From a Burr
standpoint they look pretty similar as Burr doesn't care what code you use within an action, or how you set up
your state. Each implementation has a `notebook.ipynb` that shows the basics. The `application.py` files contain extra
things like examples of `tracing` and `hooks`.

`LangChain/LCEL <https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/lcel>`_:

* .. raw:: html

    <a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/multi-agent-collaboration/lcel/notebook.ipynb">
        <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
    </a>

`Hamilton <https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/hamilton>`_:

* .. raw:: html

    <a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/multi-agent-collaboration/hamilton/notebook.ipynb">
        <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
    </a>
