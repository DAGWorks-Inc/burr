===========
Parallelism
===========

Burr allows for sets of actions/subgraphs to run in parallel. In this section we will go over the use-cases/how to run them!

General Idea/TL;DR
==================

TL;DR
-----

Burr enables graph-level parallelism by having a "parallel action" that delegates to multiple sub-actions/graphs that run in parallel.
While it has a lower-level API that's focused around tasks, Burr provides a blessed path that allows you to run multiple actions over the same
state or multiple states over the same action, and join the results together in a custom way.

``TODO -- add a diagram here``

Overview
--------

Burr allows you to define parallel actions by executing multiple individual actions or subgraphs within the context of an action,
executing them all, and joining the results. This is a simple map-reduce pattern.

Currently, Burr has two separate APIs for building parallel applications -- higher level (use this first), and lower level.
Beyond that, Burr can support parallelism however you wish to run it -- see the advanced use-cases section for more details.

Higher-level API
----------------

You select a set of "configurations" over which you want to run, and Burr launches all of them then joins the result.

This means you either:
1. Vary the state and run over the same action/subgraph (think tuning LLM parameters/inputs, running simple experiments/optimization routines, etc...)
2. Vary the action and provide the same state (think running multiple LLMs on the same input, running multiple analyses on the same data, etc...)

Note we do not distinguish between subgraph and action -- under the hood it's all treated as a "sub-application" (more on that later).

-----------------------------------------
Run the same action over different states
-----------------------------------------

For case (1) (mapping states over the same action) you implement the `MapStates` class that provides the following:

1. An ``action()`` function that provides the action/subgraph to run
2. A ``states()`` function that yields a generator of states to run over
3. A ``reduce()`` function that consumes a generator of final states (from the action/subgraph), and combines them as they come in
4. The state fields from which the action reads
5. The state fields to which the action writes


This looks as follows -- in this case we're running the same LLM over different prompts:


.. code-block:: python

    from burr.core import action, state
    from burr.core.parallelism import MapStates, RunnableGraph
    from typing import Callable, Generator, List

    @action(reads=["prompt"], writes=["llm_output"])
    def query_llm_action(state: State) -> State:
        return state.update(llm_output=_query_my_llm(prompt=state["prompt"]))

    class TestMultiplePrompts(MapStates):

        def action(self) -> Action | Callable | RunnableGraph:
            # make sure to add a name to the action
            # This is not necessary for subgraphs, as actions will already have names
            return query_llm_action.with_name("query_llm_action")

        def states(self, state: State) -> Generator[State, None, None]:
            for prompt in [
                "What is the meaning of life?",
                "What is the airspeed velocity of an unladen swallow?",
                "What is the best way to cook a steak?",
            ]:
                yield state.update(prompt=prompt)


        def reduce(self, states: Generator[State, None, None]) -> State:
            all_llm_outputs = []
            for state in states:
                all_llm_outputs.append(state["llm_output"])
            return state.update(all_llm_outputs=all_llm_outputs)

        def reads() -> List[str]:
            return ["prompts"]

        def writes() -> List[str]:
            return ["all_llm_outputs"]

Then, to run it you just treat it is an action!

.. code-block:: python

    app = (
        ApplicationBuilder()
        .with_action(
            prompt_generator=generate_prompts, # not defined above, this writes to prompts
            multi_prompt_test=TestMultiplePrompts(),
        ).with_transitions(
            ("prompt_generator", "multi_prompt_test"),
        )
        .build()
    )

-----------------------------------------
Run different actions over the same state
-----------------------------------------

For case (2) (mapping actions over the same state) you implement te `MapActions` class that provides the following:

1. A ``actions()`` function that yields a generator of actions to run
2. A ``state()`` function that provides the state to run over
3. A ``reduce()`` function that consumes a generator of final states (from the action/subgraph), and combines them as they come in
4. The state fields from which the action reads
5. The state fields to which the action writes



.. code-block:: python

    from burr.core import action, state
    from burr.core.parallelism import MapStates, RunnableGraph
    from typing import Callable, Generator, List

    @action(reads=["prompt", "model"], writes=["llm_output"])
    def query_llm(state: State, model: str) -> State:
        # TODO -- implement _query_my_llm to call litellm or something
        return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

    class TestMultipleModels(MapActions):

        def actions(self, state: State) -> Generator[Action | Callable | RunnableGraph, None, None]:
            # make sure to add a name to the action
            # This is not necessary for subgraphs, as actions will already have names
            for action in [
                query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                query_llm.bind(model="o1").with_name("o1_answer"),
                query_llm.bind(model="claude").with_name("claude_answer"),
            ]
                yield action

        def state(self, state: State) -> State::
            return state.update(prompt="What is the meaning of life?")

        def reduce(self, states: Generator[State, None, None]) -> State:
            all_llm_outputs = []
            for state in states:
                all_llm_outputs.append(state["llm_output"])
            return state.update(all_llm_outputs=all_llm_outputs)

        def reads() -> List[str]:
            return ["prompts"]

        def writes() -> List[str]:
            return ["all_llm_outputs"]


Then, it's exactly the same as above:

.. code-block:: python

    app = (
        ApplicationBuilder()
        .with_action(
            prompt_generator=generate_prompts, # not defined above, this writes to prompts
            multi_prompt_test=TestMultipleModels(),
        ).with_transitions(
            ("prompt_generator", "multi_prompt_test"),
        )
        .build()
    )


---------
Subgraphs
---------

While we've been using individual actions above, we can also replace them with subgraphs (E.G. applications inside applications).

To do this, we use the Graph API and wrap it in a RunnableGraph:

- The :py:class:`Graph <burr.core.Graph>` API allows us to tell the structure of the action
- The ``RunnableGraph`` is a wrapper that tells the framework other things you need to know to run the graph:
    - The entrypoint of the graph
    - The exit points (corresponding to ``halt_after`` in :py:meth:`run <burr.core.Application.run>`)

This might look as follows -- say we have a simple subflow that takes in a raw prompt from state and returns the LLM output:

.. code-block:: python

    from burr.core import action, state
    from burr.core.graph import Graph

    @action(reads=["prompt"], writes=["processed_prompt"])
    def process_prompt(state: State) -> State:
        processed_prompt = f"The user has asked: {state['prompt']}. Please respond directly to that prompt, but only in riddles."
        return state.update(
            prompt=state["prompt"],
        )

    @action(reads=["processed_prompt"], writes=["llm_output"])
    def query_llm(state: State) -> State:
        return state.update(llm_output=_query_my_llm(prompt=state["processed_prompt"]))

    graph = (
        GraphBuilder()
        .with_action(
            process_prompt=process_prompt,
            query_llm=query
        ).with_transitions(
            ("process_prompt", "query_llm")
        ).build()
    )

    runnable_graph = RunnableGraph(
        graph=graph,
        entrypoint="process_prompt",
        halt_after="query_llm"
    )

    class TestMultiplePromptsWithSubgraph(MapStates):

        def action(self) -> Action | Callable | RunnableGraph:
            return runnable_graph

        def states(self, state: State) -> Generator[State, None, None]:
            for prompt in [
                "What is the meaning of life?",
                "What is the airspeed velocity of an unladen swallow?",
                "What is the best way to cook a steak?",
            ]:
                yield state.update(prompt=prompt)

        ... # same as above

In the code above, we're effectively treating the graph like an action -- due to the single entrypoint/halt_after condition we specified,
it can run just as the single prompt we did above can. Note this is also doable for running multiple actions over the same state.


--------------
Passing inputs
--------------

.. note::

    Should ``MapOverInputs`` be its own class? Or should we have ``bind_from_state(prompt="prompt_field_in_state")`` that allows you to pass it in as
    state and just use the mapping capabilities?

Each of these can (optionally) produce ``inputs`` by yielding/returning a tuple from the ``states``/``actions`` function.

This is useful if you want to vary the inputs. Note this is the same as passing ``inputs=`` to app.run.


.. code-block:: python

    from burr.core import action, state
    from burr.core.graph import Graph

    @action(reads=["prompt"], writes=["processed_prompt"])
    def process_prompt(state: State) -> State:
        processed_prompt = f"The user has asked: {state['prompt']}. Please respond directly to that prompt, but only in riddles."
        return state.update(
            prompt=state["prompt"],
        )

    @action(reads=["processed_prompt"], writes=["llm_output"])
    def query_llm(state: State, model: str) -> State:
        return state.update(llm_output=_query_my_llm(prompt=state["processed_prompt"], model=model))

    graph = (
        GraphBuilder()
        .with_action(
            process_prompt=process_prompt,
            query_llm=query
        ).with_transitions(
            ("process_prompt", "query_llm")
        ).build()
    )

    runnable_graph = RunnableGraph(
        graph=graph,
        entrypoint="process_prompt",
        halt_after="query_llm"
    )

    class TestMultiplePromptsWithSubgraph(MapStates):

        def action(self) -> Action | Callable | RunnableGraph:
            return runnable_graph

        def states(self, state: State) -> Generator[State, None, None]:
            for prompt in [
                "What is the meaning of life?",
                "What is the airspeed velocity of an unladen swallow?",
                "What is the best way to cook a steak?",
            ]:
                yield state.update(prompt=prompt), {"model": "gpt-4"} # pass in the model as an input

        ... # same as above

----------------------
Full cartesian product
----------------------

If you want to run all possible combinations of actions/states, you can use the ``MapActionsAndStates`` class  -- this is actually the
base class for the above two classes. For this, you provide a generator of actions and a generator of states, and Burr will run all possible
combinations.

For tracking which states/actions belong to which actions, we recommend you use the values stored in the state (see example).

.. code-block:: python

    from burr.core import action, state
    from burr.core.parallelism import MapStates, RunnableGraph
    from typing import Callable, Generator, List

    @action(reads=["prompt", "model"], writes=["llm_output"])
    def query_llm(state: State, model: str) -> State:
        # TODO -- implement _query_my_llm to call litellm or something
        return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

    class TestMultipleModels(MapActions):

        def actions(self, state: State) -> Generator[Action | Callable | RunnableGraph, None, None]:
            # make sure to add a name to the action
            # This is not necessary for subgraphs, as actions will already have names
            for action in [
                query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                query_llm.bind(model="o1").with_name("o1_answer"),
                query_llm.bind(model="claude").with_name("claude_answer"),
            ]
                yield action

        def states(self, state: State) -> Generator[State, None, None]:
            for prompt in [
                "What is the meaning of life?",
                "What is the airspeed velocity of an unladen swallow?",
                "What is the best way to cook a steak?",
            ]:
                yield state.update(prompt=prompt)

        def reduce(self, states: Generator[State, None, None]) -> State:
            all_llm_outputs = []
            for state in states:
                all_llm_outputs.append(
                    {
                        "output" : state["llm_output"],
                        "model" : state["model"],
                        "prompt" : state["prompt"],
                    }
                )
            return state.update(all_llm_outputs=all_llm_outputs)

        def reads() -> List[str]:
            return ["prompts"]

        def writes() -> List[str]:
            return ["all_llm_outputs"]


Lower-level API
---------------

The above compile into a set of "tasks" -- sub-applications to run. If, however, you want to have more control, you
can use the lower-level API to simply define the tasks. This allows you to provide any combination of actions, input, and state
to the tasks.

For those who are curious, this is what the above APIs extend from.

.. code-block:: python

    from burr.core import action, state, ApplicationContext
    from burr.core.parallelism import MapStates, RunnableGraph
    from typing import Callable, Generator, List

    @action(reads=["prompt", "model"], writes=["llm_output"])
    def query_llm(state: State, model: str) -> State:
        # TODO -- implement _query_my_llm to call litellm or something
        return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

    class MultipleTaskExample(TaskBasedParallelAction):
        def tasks(state: State, context: ApplicationContext) -> Generator[SubGraphTask]:
            for prompt in state["prompts"]:
                for action in [
                    query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                    query_llm.bind(model="o1").with_name("o1_answer"),
                    query_llm.bind(model="claude").with_name("claude_answer"),
                ]
                    yield SubGraphTask(
                        action=action, # can be a RunnableGraph as well
                        state=state.update(prompt=prompt),
                        inputs={},
                        # stable hash -- up to you to ensure uniqueness
                        application_id=hashlib.sha256(context.application_id + action.name + prompt).hexdigest(),
                        # a few other parameters -- see advanced usage -- failure conditions, etc...
                    )

        def reduce(self, states: Generator[State, None, None]) -> State:
            all_llm_outputs = []
            for state in states:
                all_llm_outputs.append(
                    {
                        "output" : state["llm_output"],
                        "model" : state["model"],
                        "prompt" : state["prompt"],
                    }
                )
            return state.update(all_llm_outputs=all_llm_outputs)


Advanced usage
--------------

We anticipate the above should cover most of what you want to do, but we have a host of advanced tuning capabilities.

---------
Execution
---------

To enable execution, you need to pass a ``burr.Executor`` to the application, or to the actions themselves. We have a few available executors:

- ``burr.parallelism.MultiThreadedExecutor`` -- runs the tasks in parallel using threads (default)
- ``burr.parallelism.MultiProcessExecutor`` -- runs the tasks in parallel using processes
- ``burr.parallelism.RayExecutor`` -- runs the tasks in parallel using `Ray <https://docs.ray.io/en/latest/index.html>`_
- ``burr.parallelism.Dask`` -- runs the tasks in parallel using `Dask <https://dask.org/>`_

For async, we only allow the ``burr.parallelism.AsyncExecutor`` (default), which uses ``asyncio.gather`` to run the tasks in parallel.

You can pass this either as a global executor for the application, or specify it as part of your class:

Specifying it as part of the application -- will get routed as the default to all parallel actions:

.. code-block:: python

    app = (
        ApplicationBuilder()
        .with_executor(MultiThreadedExecutor(max_concurrency=10))
        .build()
    )

Specifying it as part of the action -- will override the global executor:

.. code-block:: python

    class TestMultiplePrompts(MapStates):

        def action(self) -> Action | Callable | RunnableGraph:
            return runnable_graph

        def executor(self) -> Executor:
            return MultiThreadedExecutor(max_concurrency=10)

        ... # same as above


--------------------
Persistence/tracking
--------------------

By default, the trackers/persisters will be passed from the parent application to the child application. The application IDs
will form a stable hash (presuming the order is constant) to ensure that the same application ID is used for the same task every time.

It will also utilize the same persister to load from the prior state, if that is used on the application level (see the state-persistence section).

This enables the following:

1. Tracking will automatically be associated with the same application (and sub-application) when reloaded
2. If the concurrent application quits halfway through, bthe application will be able to pick up where it left off, as will all sub-applications

You can disable either tracking or persistence at the sub-application level by passing ``track=False`` or ``persist=False`` to the constructor of the application method.

You can also disable it globally using the application builder:

.. code-block:: python

    class TestMultiplePrompts(MapStates):

        def action(self) -> Action | Callable | RunnableGraph:
            return runnable_graph

        def tracker(self, context: ApplicationContext) -> TrackingBehavior | None:
            # return "cascade" # default
            # return None # no tracking
            return LocalTrackingClient(...) # custom tracker

        def persister(self, context: ApplicationContext) -> Persister | None:
            # return "cascade" # default
            # return None # no persistence
            return SQLLitePersister(...) # custom persister

        ... # same as above

-----
Other
-----

Things we will consider after the MVP:

- Streaming -- interleaving parallel streaming actions and giving results as they come
- Iteration of sub-action results (see recipe in advanced use-cases)


Under the hood
==============

Under the hood, all this does is simplify the :ref:`recursion <recursion>`: API to allow for multiple actions to be run in parallel.

- ``RunnableGraph`` s are set as subgraphs, and recursively executed by the application, using the executor
- ``Action`` s are turned into ``RunnableGraph`` s by the framework, and executed by the executor

In the UI, this will show up as a "child" application -- see the :ref:`recursion <recursion>`: section for more details.

The "global" executor you specify will get passed to the application's


Advanced use-Cases
==================

As this is all just syntactic sugar for recursion, you can use the basic capabilities to get more advanced capabilities.

This involves instantiating a sub-application inside the action, and running it yourself.


Interleaving generators
-----------------------

Say you want to provide an agent that provides up-to-date progress on it's thoughts. For example, say you want to providea
a planning agent with a similar interface to OpenAI's o1 model.


To do this, you would typically call to :py:meth:`iterate <burr.core.application.Application.iterate>`. Now, say you wanted to run
multiple in parallel!

While this is not built to be easy with the APIs in this section, it's very doable with the underlying recursion API.

The basics (code not present now):

1. Create each sub-application using the ``with_parent_context`` method
2. Run each sub-application in parallel using the executor
3. Combine the generators in parallel, yielding results as they come out


Inter-action communication
--------------------------

Note you can do the above and have one action proceed depending on the result of the other action.

Just add another step!

4. If the desired condition is met, cancel the other one and return with the function
