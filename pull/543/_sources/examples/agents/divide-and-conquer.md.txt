# Divide and Conquer

A single agent can usually operate effectively using a handful of tools within a single domain, but even using powerful models like `gpt-4`, it can be less effective at using many tools.

One way to approach complicated tasks is through a "divide-and-conquer" approach: create a "specialized agent" for each task or domain and route tasks to the correct "expert". This means that each agent can become a sequence of LLM calls that chooses how to use a specific "tool".

The examples we link to below are inspired by the paper [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation by Wu, et. al.](https://arxiv.org/abs/2308.08155).
They can be found in [this part of our repository](https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration).

![](./_divide-and-conquer.png)

We provide two implementations of this idea: with [Hamilton](https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/hamilton) and with [LangChain LCEL](https://github.com/DAGWorks-Inc/burr/tree/main/examples/multi-agent-collaboration/lcel). From Burr's standpoint, both look similar and you're free to use your preferred framework within an `action`.

## With Hamilton

<a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/multi-agent-collaboration/hamilton/notebook.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>



## With LangChain Expression Language (LCEL)

<a target="_blank" href="https://colab.research.google.com/github/dagworks-inc/burr/blob/main/examples/multi-agent-collaboration/lcel/notebook.ipynb">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
