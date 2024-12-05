====================
Planned Capabilities
====================

These are on the roadmap (and will be part of Burr in the imminent future), but have not been built yet.

We build fast though, so let us know which ones you need and they'll be in there before you know it!


------------------------------------
Evaluation & Annotation integrations
------------------------------------

You can already annotate with the Burr UI. We have plans to:

1. plug in metrics and custom callbacks/LLM as judge capabilities to enable you to evaluate what captured and annotated.
2. SDK functionality to allow programmatic annotation and evaluation, as well as export and search of annotations.

-----------------------------
State Management/Immutability
-----------------------------

We plan the ability to manage state in a few ways:

1. ``commit`` -- an internal tool to commit/compile a series of changes so that we have the latest state evaluated
2. ``persist`` -- a user-facing API to persist state to a database. This will be pluggable by the user, and we will have a few built-in options (e.g. a simple in-memory store, a file store, a database store, etc...)
3. ``hydrate`` -- a static method to hydrate state from a database. This will be pluggable by the user, and we will have a few built-in options that mirror those in ``persist`` options.

Currently state is immutable, but it utilizes an inefficient copy mechanism. This is out of expedience -- we don't anticipate this will
be painful for the time being, but plan to build a more efficient functional paradigm. We will likely have:

1. Each state object be a node in a linked list, with a pointer to the previous state. It carries a diff of the changes from the previous state.
2. An ability to ``checkpoint`` (allowing for state garbage collection), and store state in memory/kill out the pointers.

We will also consider having the ability to have a state solely backed by redis (and not memory), but we are still thinking through the API.

----------------------
Compilation/Validation
----------------------

We currently do not validate that the chain of actions provide a valid state, although we plan to walk the graph to ensure that no "impossible"
situation is reached. E.G. if an action reads from a state that is not written to (or not initialized), we will raise an error, likely upon calling `validate`.
We may be changing the behavior with defaults over time.

--------------------
Exception Management
--------------------

Currently, exceptions will break the control flow of an action, stopping the program early. Thus,
if an exception is expected, the program will stop early. We will be adding the ability to conditionally transition based
on exceptions, which will allow you to transition to an error-handling (or retry) action that does not
need the full outputs of the prior action.

Here is what it would look like in the current API:

.. code-block:: python

    @action(reads=["attempts"], writes=["output", "attempts"])
    def some_flaky_action(state: State, max_retries: int=3) -> State:
        result = {"output": None, "attempts": state["attempts"] + 1}
        try:
            result["output"] = call_some_api(...)
        except APIException as e:
            if state["attempts"] >= max_retries:
               raise e
        return state.update(**result)

One could imagine adding it as a condition (a few possibilities)

.. code-block:: python

    @action(reads=[], writes=["output"])
    def some_flaky_action(state: State) -> State
        result = {"output": call_some_api(...)}
        return state.update(**result)

    builder.with_actions(
       some_flaky_action=some_flaky_action
    ).with_transitions(
       (
          "some_flaky_action",
          "some_flaky_action",
          error(APIException) # infinite retries
          error(APIException, max=3) # 3 visits to this edge then it gets reset if this is not chosen
          # That's stored in state
       )
    )

Will have to come up with ergonomic APIs -- the above are just some ideas.

------------
Integrations
------------

We already have support for Haystack, Hamilton, and LangChain.
Please request any other integrations you'd like to see.
