# Burr
<div>
<a href="https://discord.gg/6Zy2DwP4f3" target="_blank"><img src="https://img.shields.io/badge/Join-Burr_Discord-brightgreen?logo=discord" alt="Burr Discord"/></a>
</div>

Burr makes it easy to develop applications that make decisions based on state (chatbots, agents, simulations, etc...) from simple python building blocks.
Burr includes a UI that can track/monitor those decisions in real time.

Link to [documentation](https://burr.dagworks.io/). Quick (<3min) video intro [here](https://www.loom.com/share/a10f163428b942fea55db1a84b1140d8?sid=1512863b-f533-4a42-a2f3-95b13deb07c9).
Longer [video intro & walkthrough](https://www.youtube.com/watch?v=rEZ4oDN0GdU). Blog post [here](https://blog.dagworks.io/p/burr-develop-stateful-ai-applications).

## 🏃Quick start

Install from `pypi`:

```bash
pip install "burr[start]"
```

Then run the UI server:

```bash
burr
```
This will open up Burr's telemetry UI. It comes loaded with some default data so you can click around.
It also has a demo chat application to help demonstrate what the UI captures enabling you too see things changing in
real-time. Hit the "Demos" side bar on the left and select `chatbot`. To chat it requires the `OPENAI_API_KEY`
environment variable to be set, but you can still see how it works if you don't have an API key set.

Next, start coding / running examples:

```bash
git clone https://github.com/dagworks-inc/burr && cd burr/examples/hello-world-counter
python application.py
```
You'll see the counter example running in the terminal, along with the trace being tracked in the UI.
See if you can find it.

For more details see the [getting started guide](https://burr.dagworks.io/getting_started/simple-example/).

## 🔩 How does Burr work?

With Burr you express your application as a state machine (i.e. a graph/flowchart).
You can (and should!) use it for anything where managing state can be hard. Hint: managing state is always hard!
This is true across a wide array of contexts, from building RAG applications to power a chatbot, to running ML parameter tuning/evaluation workflows,
to conducting a complex forecasting simulation.

Burr includes:

1. A (dependency-free) low abstraction python library that enables you to build and manage state machines with simple python functions
2. A UI you can use view execution telemetry for introspection and debugging
3. A set of integrations to make it easier to persist state, connect to telemetry, and integrate with other systems

![Burr at work](./chatbot.gif)

## 💻️ What can you do with Burr?

Burr can be used to power a variety of applications, including:

1. [A simple gpt-like chatbot](examples/multi-modal-chatbot)
2. [A stateful RAG-based chatbot](examples/conversational-rag)
3. [A machine learning pipeline](examples/ml-training)
4. [A simulation](examples/simulation)

And a lot more!

Using hooks and other integrations you can (a) integrate with any of your favorite vendors (LLM observability, storage, etc...), and
(b) build custom actions that delegate to your favorite libraries (like [Hamilton](https://github.com/DAGWorks-Inc/hamilton)).

Burr will _not_ tell you how to build your models, how to query APIs, or how to manage your data. It will help you tie all these together
in a way that scales with your needs and makes following the logic of your system easy. Burr comes out of the box with a host of integrations
including tooling to build a UI in streamlit and watch your state machine execute.

## 🏗 Start Building

See the documentation for [getting started](https://burr.dagworks.io/getting_started/simple-example), and follow the example.
Then read through some of the concepts and write your own application!

## 📃 Comparison against common frameworks

While Burr is attempting something (somewhat) unique, there are a variety of tools that occupy similar spaces:

| Criteria                                  | Burr | Langgraph | temporal | Langchain | Superagent | Hamilton |
|-------------------------------------------|:---:|:----------:|:--------:|:---------:|:----------:|:--------:|
| Explicitly models a state machine         | ✅  |      ✅    |    ❌    |     ❌    |     ❌     |   ❌     |
| Framework-agnostic                        | ✅  |      ✅    |    ✅    |     ✅    |     ❌     |   ✅     |
| Asynchronous event-based orchestration    | ❌  |      ❌    |    ✅    |     ❌    |     ❌     |   ❌     |
| Built for core web-service logic          | ✅  |      ✅    |    ❌    |     ✅    |     ✅     |   ✅     |
| Open-source user-interface for monitoring | ✅  |      ❌    |    ❌    |     ❌    |     ❌     |   ❌     |
| Works with non-LLM use-cases              | ✅  |      ❌    |    ❌    |     ❌    |     ❌     |   ✅     |

## 🌯 Why the name Burr?

Burr is named after [Aaron Burr](https://en.wikipedia.org/wiki/Aaron_Burr), founding father, third VP of the United States, and murderer/arch-nemesis of [Alexander Hamilton](https://en.wikipedia.org/wiki/Alexander_Hamilton).
What's the connection with Hamilton? This is [DAGWorks](www.dagworks.io)' second open-source library release after the [Hamilton library](https://github.com/dagworks-inc/hamilton)
We imagine a world in which Burr and Hamilton lived in harmony and saw through their differences to better the union. We originally
built Burr as a _harness_ to handle state between executions of Hamilton DAGs (because DAGs don't have cycles),
but realized that it has a wide array of applications and decided to release it more broadly.

## 🛣 Roadmap

While Burr is stable and well-tested, we have quite a few tools/features on our roadmap!

1. Testing & eval curation. Curating data with annotations and being able to export these annotations to create unit & integration tests.
2. Various efficiency/usability improvements for the core library (see [planned capabilities](https://burr.dagworks.io/concepts/planned-capabilities/) for more details). This includes:
   1. Fully typed state with validation
   2. First-class support for retries + exception management
   3. More integration with popular frameworks (LCEL, LLamaIndex, Hamilton, etc...)
   4. Capturing & surfacing extra metadata, e.g. annotations for particular point in time, that you can then pull out for fine-tuning, etc.
3. Cloud-based checkpointing/restart for debugging or production use cases (save state to db and replay/warm start, backed by a configurable database)
4. Tooling for hosted execution of state machines, integrating with your infrastructure (Ray, modal, FastAPI + EC2, etc...)
5. Storage integrations. More integrations with technologies like Redis, MongoDB, MySQL, etc. so you can run Burr on top of what you have available.

If you want to avoid self-hosting the above solutions we're building Burr Cloud. To let us know you're interested
 sign up [here](https://forms.gle/w9u2QKcPrztApRedA) for the waitlist to get access.

## 🤲 Contributing

We welcome contributors! To get started on developing, see the [developer-facing docs](https://burr.dagworks.io/contributing).

## 👪 Contributors

### Code contributions

Users who have contributed core functionality, integrations, or examples.
- [Elijah ben Izzy](https://github.com/elijahbenizzy)
- [Stefan Krawczyk](https://github.com/skrawcz)
- [Joseph Booth](https://github.com/jombooth)
- [Nandani Thakur](https://github.com/NandaniThakur)

### Bug hunters/special mentions
Users who have contributed small docs fixes, design suggestions, and found bugs
- [Thierry Jean](https://github.com/zilto)
- [Luke Chadwick](https://github.com/vertis)
- [Evans](https://github.com/sudoevans)
