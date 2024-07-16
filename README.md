# 🧊 Burr
<div align="center">
<a href="https://discord.gg/6Zy2DwP4f3" target="_blank"><img src="https://img.shields.io/badge/Join-Burr_Discord-brightgreen?logo=discord" alt="Burr Discord"/></a>
<img src="https://github.com/user-attachments/assets/2ab9b499-7ca2-4ae9-af72-ccc775f30b4e" width=200 height=200/>
</div>

Burr makes it easy to develop applications that make decisions (chatbots, agents, simulations, etc...) from simple python building blocks.

Burr works well for any application that uses LLMs, and can integrate with any of your favorite frameworks. Burr includes a UI that can track/monitor your system in real time.

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
You can (and should!) use it for anything in which you have to manage state, track complex decisions, add human feedback, or dictate an idempotent, self-persisting workflow.

The core API is simple -- the Burr hello-world looks like this (plug in your own LLM, or copy from [the docs](https://burr.dagworks.io/getting_started/simple-example/#build-a-simple-chatbot>) for _gpt-X_)

```python
from burr.core import action, State, ApplicationBuilder

@action(reads=[], writes=["prompt", "chat_history"])
def human_input(state: State, prompt: str) -> State:
    # your code -- write what you want here!
    return state.update(prompt=prompt).append(chat_history=chat_item)

@action(reads=["chat_history"], writes=["response", "chat_history"])
def ai_response(state: State) -> State:
    response = _query_llm(state["chat_history"]) # Burr doesn't care how you use LLMs!
    return state.update(response=content).append(chat_history=chat_item)

app = (
    ApplicationBuilder()
    .with_actions(human_input, ai_response)
    .with_transitions(
        ("human_input", "ai_response"),
        ("ai_response", "human_input")
    ).with_state(chat_history=[])
    .with_entrypoint("human_input")
    .build()
)
*_, state = app.run(halt_after=["ai_response"], inputs={"prompt": "Who was Aaron Burr, sir?"})
print("answer:", app.state["response"])
```

Burr includes:

1. A (dependency-free) low-abstraction python library that enables you to build and manage state machines with simple python functions
2. A UI you can use view execution telemetry for introspection and debugging
3. A set of integrations to make it easier to persist state, connect to telemetry, and integrate with other systems

![Burr at work](https://github.com/DAGWorks-Inc/burr/blob/main/chatbot.gif)

## 💻️ What can you do with Burr?

Burr can be used to power a variety of applications, including:

1. [A simple gpt-like chatbot](https://github.com/dagworks-inc/burr/tree/main/examples/multi-modal-chatbot)
2. [A stateful RAG-based chatbot](https://github.com/dagworks-inc/burr/tree/main/examples/conversational-rag/simple_example)
3. [An LLM-based adventure game](https://github.com/DAGWorks-Inc/burr/tree/main/examples/llm-adventure-game)
4. [An interactive assistant for writing emails](https://github.com/DAGWorks-Inc/burr/tree/main/examples/email-assistant)

As well as a variety of (non-LLM) use-cases, including a time-series forecasting [simulation](https://github.com/DAGWorks-Inc/burr/tree/main/examples/simulation),
and [hyperparameter tuning](https://github.com/DAGWorks-Inc/burr/tree/main/examples/ml-training).

And a lot more!

Using hooks and other integrations you can (a) integrate with any of your favorite vendors (LLM observability, storage, etc...), and
(b) build custom actions that delegate to your favorite libraries (like [Hamilton](https://github.com/DAGWorks-Inc/hamilton)).

Burr will _not_ tell you how to build your models, how to query APIs, or how to manage your data. It will help you tie all these together
in a way that scales with your needs and makes following the logic of your system easy. Burr comes out of the box with a host of integrations
including tooling to build a UI in streamlit and watch your state machine execute.

## 🏗 Start building

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
| Open-source user-interface for monitoring | ✅  |      ❌    |    ❌    |     ❌    |     ❌     |   ✅     |
| Works with non-LLM use-cases              | ✅  |      ❌    |    ❌    |     ❌    |     ❌     |   ✅     |

## 🌯 Why the name Burr?

Burr is named after [Aaron Burr](https://en.wikipedia.org/wiki/Aaron_Burr), founding father, third VP of the United States, and murderer/arch-nemesis of [Alexander Hamilton](https://en.wikipedia.org/wiki/Alexander_Hamilton).
What's the connection with Hamilton? This is [DAGWorks](www.dagworks.io)' second open-source library release after the [Hamilton library](https://github.com/dagworks-inc/hamilton)
We imagine a world in which Burr and Hamilton lived in harmony and saw through their differences to better the union. We originally
built Burr as a _harness_ to handle state between executions of Hamilton DAGs (because DAGs don't have cycles),
but realized that it has a wide array of applications and decided to release it more broadly.

## 🛣 Roadmap

While Burr is stable and well-tested, we have quite a few tools/features on our roadmap!

1. Recursive state machines. Run Burr within Burr to get hierarchical agents/parallelism + track through to the UI.
2. Testing & eval curation. Curating data with annotations and being able to export these annotations to create unit & integration tests.
3. Various efficiency/usability improvements for the core library (see [planned capabilities](https://burr.dagworks.io/concepts/planned-capabilities/) for more details). This includes:
   1. Fully typed state with validation
   2. First-class support for retries + exception management
   3. More integration with popular frameworks (LCEL, LLamaIndex, Hamilton, etc...)
   4. Capturing & surfacing extra metadata, e.g. annotations for particular point in time, that you can then pull out for fine-tuning, etc.
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
- [Thierry Jean](https://github.com/zilto)
- [Hamza Farhan](https://github.com/HamzaFarhan)

### Bug hunters/special mentions
Users who have contributed small docs fixes, design suggestions, and found bugs
- [Luke Chadwick](https://github.com/vertis)
- [Evans](https://github.com/sudoevans)
- [Sasmitha Manathunga](https://github.com/mmz-001)
