=======
Actions
=======

.. _actions:


Actions do the heavy-lifting in a workflow. They should contain all complex compute. You can define actions
either through a class-based or function-based API. If actions implement `async def run` then will be run in an
asynchronous context (and thus require one of the async application functions).

Actions have two primary responsibilities:

1. ``run`` -- compute a result
2. ``update`` -- modify the state

The ``run`` method should return a dictionary of the result and the ``update`` method should return
the updated state. They declare their dependencies so the framework knows *which* state variables they read and write. This allows the
framework to optimize the execution of the workflow. We call (1) a ``Function`` and (2) a ``Reducer`` (similar to `Redux <https://redux.js.org/>`_, if you're familiar with frontend UI technology).

.. _inputref:

--------------
Runtime inputs
--------------

Actions can declare inputs that are not part of the state. This is for the case that you want to pause workflow execution for human input.

For instance, say you have a chatbot. The first step will declare the ``input`` parameter ``prompt`` -- it will take that, process it, and put
it in the state. The subsequent steps will read the result of that from state.

There are two APIs for defining actions: class-based and function-based. They are largely equivalent, but differ in use.

- use the function-based API when you want to write something quick and terse that reads from a fixed set of state variables
- use the class-based API when you want to leverage inheritance or parameterize the action in more powerful ways

-------------------
Class-based actions
-------------------

You can define an action by implementing the ``Action`` class:

.. code-block:: python

    from burr.core import Action, State

    class CustomAction(Action):
        @property
        def reads(self) -> list[str]:
            return ["var_from_state"]

        def run(self, state: State) -> dict:
            return {"var_to_update": state["var_from_state"] + 1}

        @property
        def writes(self) -> list[str]:
            return ["var_to_update"]

        def update(self, result: dict, state: State) -> State:
            return state.update(**result)

You then pass the action to the ``ApplicationBuilder``:

.. code-block:: python

    from burr.core import ApplicationBuilder

    app = ApplicationBuilder().with_actions(
        custom_action=CustomAction()
    )...


Note that if the action has inputs, you have to define the optional `inputs` property:

.. code-block:: python

    from burr.core import Action, State

    class CustomAction(Action):
        @property
        def reads(self) -> list[str]:
            return ["var_from_state"]

        def run(self, state: State, increment_by: int) -> dict:
            return {"var_to_update": state["var_from_state"] + increment_by}

        @property
        def writes(self) -> list[str]:
            return ["var_to_update"]

        def update(self, result: dict, state: State) -> State:
            return state.update(**result)

        @property
        def inputs(self) -> list[str]:
            return ["increment_by"]


----------------------
Function-based actions
----------------------

You can also define actions by decorating a function with the `@action` decorator:

.. code-block:: python

    from burr.core import action, State

    @action(reads=["var_from_state"], writes=["var_to_update"])
    def custom_action(state: State) -> Tuple[dict, State]:
        result = {"var_to_update": state["var_from_state"] + 1}
        return result, state.update(**result)

    app = ApplicationBuilder().with_actions(
        custom_action=custom_action
    )...

Function-based actions can take in parameters which are akin to passing in constructor parameters. This is done through the `bind` method:

.. code-block:: python

    @action(reads=["var_from_state"], writes=["var_to_update"])
    def custom_action(state: State, increment_by: int) -> Tuple[dict, State]:
        result = {"var_to_update": state["var_from_state"] + increment_by}
        return result, state.update(**result)

    app = ApplicationBuilder().with_actions(
        custom_action=custom_action.bind(increment_by=2)
    )...

This is the same as ``functools.partial``, but it is more explicit and easier to read. If an action has parameters that are not
bound, they will be referred to as inputs. For example:


.. code-block:: python

    @action(reads=["var_from_state"], writes=["var_to_update"])
    def custom_action(state: State, increment_by: int) -> Tuple[dict, State]:
        result = {"var_to_update": state["var_from_state"] + increment_by}
        return result, state.update(**result)

    app = ApplicationBuilder().with_actions(
        custom_action=custom_action
    )...

Will require the inputs to be passed in at runtime.

Note that these combine the ``reduce`` and ``run`` methods into a single function, and they're both returned at the same time.

-----------
``Inputs``
-----------

If you simply want a node to take in inputs and pass them to the state, you can use the `Input` action:

.. code-block:: python

    app = ApplicationBuilder().with_actions(
        get_input=Input("var_from_state")
    )...

This will look for the `var_from_state` in the inputs and pass it to the state. Note this is just syntactic sugar
for declaring inputs through one of the other APIs and adding it to state -- if you want to do anything more complex
with the input, you should use other APIs.

-----------
``Results``
-----------

If you just want to fill a result from the state, you can use the `Result` action:

.. code-block:: python

    app = ApplicationBuilder().with_actions(
        get_result=Result("var_from_state")
    )...


This simply grabs the value from the state and returns it as the result. It is purely a placeholder
for an action that should just use the result, although you do not need it.

Refer to :ref:`actions <actions>` for documentation.
