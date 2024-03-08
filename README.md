# Burr

## What is Burr?

Burr is a way to express a state machine (i.e. a graph/flowchart) for data/AI projects. You can (and should!) use it for anything where managing state can be hard. Hint: managing state
is always hard! This is true across a wide array of contexts, from building RAG applications to power a chatbot, to running an ML parameter tuning/evaluation workflow, to rhnming a complex forecasting simulation

Link to [documentation](https://burr.dagworks.io/). Quick video intro [here](https://www.loom.com/share/8a92474bb7574d6eb4cd25c21913adf2).

Burr is:
1. A (dependency-free) low abstraction python library that enables you to build and manage state machines with simple python functions
2. It comes with a UI you can use view execution telemetry for introspection and debugging

## What can you do with Burr?

Burr can be used for a variety of applications. Burr can build a state machine to orchestrate, express, and track:

1. [A gpt-like chatbot](examples/gpt)
2. [A machine learning pipeline](examples/ml_training)
3. [A trading simulation](examples/simulation)

And a lot more!

Using hooks and other integrations you can (a) integrate with any of your favorite vendors (LLM observability, storage, etc...), and
(b) build custom actions that delegate to your favorite libraries (like [Hamilton](github.com/DAGWorks-Inc/hamilton)).

Burr will _not_ tell you how to build your models, how to query APIs, or how to manage your data. It will help you tie all these together
in a way that scales with your needs and makes following the logic of your system easy. Burr comes out of the box with a host of integrations
including tooling to build a UI in streamlit and watch your state machine execute.

![Burr at work](./chatbot.gif)

## Why the name Burr?

Burr is named after [Aaron Burr](https://en.wikipedia.org/wiki/Aaron_Burr), founding father, third VP of the United States, and murderer/arch-nemesis of [Alexander Hamilton](https://en.wikipedia.org/wiki/Alexander_Hamilton).
What's the connection with Hamilton? This is [DAGWorks](www.dagworks.io)' second open-source library release after the [Hamilton library](https://github.com/dagworks-inc/hamilton)
Here we imagine a world in which Burr and Hamilton lived in harmony and saw through their differences and thus were happy to work together. We originally
built Burr as a _harness_ to handle state between executions of Hamilton DAGs (because DAGs don't have cycles),
but realized that it has a wide array of applications and decided to release it more broadly.

# Getting Started

To get started, install from `pypi`, using your favorite package manager:

```bash
pip install "burr[start]"
```

This includes the dependencies for the tracking server (see next step) -- alternatively if you want the core library only then just run `pip install burr`.
Then, run the server and check out the demo projects:

```bash
$ burr

2024-02-23 11:43:21.249 | INFO     | burr.cli.__main__:run_server:88 - Starting server on port 7241
```

This will start a server and open up a browser window with a few demo projects preloaded for you to play with.

Next, see the documentation for [getting started](https://burr.dagworks.io/getting_started/simple-example.html), and follow the example.
Then read through some of the concepts and write your own application!

# Roadmap

While Burr is stable and well-tested, we have quite a few tools/features on our roadmap!

1. Various efficiency/usability improvements for the core library (see [planned capabilities](https://burr.dagworks.io/concepts/planned-capabilities.html) for more details). This includes:
   1. Fully typed state with validation
   2. First-class support for retries + exception management
   3. More integration with popular frameworks (LCEL, LLamaIndex, Hamilton, etc...)
   4. Capturing & surfacing extra metadata, e.g. annotations for particular point in time, that you can then pull out for fine-tuning, etc.
2. Cloud-based checkpointing/restart for debugging or production use cases (save state to db and replay/warm start, backed by a configurable database)
3. Tooling for hosted execution of state machines, integrating with your infrastructure (Ray, modal, FastAPI + EC2, etc...)

If you want to avoid self-hosting the above solutions we're building Burr Cloud. To let us know you're interested
 sign up [here](https://forms.gle/w9u2QKcPrztApRedA) for the waitlist to get access.

# Contributing

We welcome contributors! To get started on developing, see the [developer-facing docs](https://burr.dagworks.io/contributing).

## Contributors
- [Elijah ben Izzy](https://github.com/elijahbenizzy)
- [Stefan Krawczyk](https://github.com/skrawcz)
- [Joseph Booth](https://github.com/jombooth)
- [Thierry Jean](https://github.com/zilto)
