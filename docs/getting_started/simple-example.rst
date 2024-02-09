.. _simpleexample:

=================
Simple Example
=================
This simple example is just to learn the basics of the library. The application we're building is not particularly interesting,
but it will get you powerful. If you want to skip ahead to the cool stuff (chatbots,
ML training, simulations, etc...) feel free to jump into the deep end and start with the :ref:`examples <examples>`.

We will go over enough of the concepts to help you understand the code, but there is a much more in-depth set of
explanations in the :ref:`concepts <concepts>` section.

------------------
Build a Counter
------------------
We're going to build a counter application. This counter will count to 10 and then stop.

Let's start by defining some actions, the building-block of Burr. You can think of actions as a function that
computes a result and modifies state. They declare what they read and write.

Let's define two actions:
1. A counter action that increments the counter
2. A printer action that prints the counter


.. code-block:: python

    @action(reads=["counter"], writes=["counter"])
    def count(state: State) -> Tuple[dict, State]:
        current = state["counter"] + 1
        result = {"counter": current}
        print("counted to ", current)
        return result, state.update(**result) # return both the intermediate

    @action(reads=["counter"], writes=[])
    def done(state: State) -> Tuple[dict, State]:
        print("Bob's your uncle")
        return {}, state

This is an action that reads the "counter" from the state, increments it by 1, and then writes the new value back to the state.
It returns both the intermediate result (``result``) and the updated state.

Next, let's put together our application. To do this, we'll use an ``ApplicationBuilder``

.. code-block:: python

    from burr.core import ApplicationBuilder, default, expr
    app = (
        ApplicationBuilder()
        .with_state(counter=0) # initialize the count to zero
        .with_actions(
            count=count, # add the counter action with the name "counter"
            done=done # add the printer action with the name "printer"
        ).with_transitions(
            ("count", "count", expr("counter < 10")), # Keep counting if the counter is less than 10
            ("count", "done", default) # Otherwise, we're done
        ).with_entrypoint("count") # we have to start somewhere
        .build()
    )


We can visualize the application (note you need ``burr[graphviz]`` installed):

.. code-block:: python

    app.visualize("./graph", format="png", include_conditions=True, include_state=True)

.. image:: ../_static/counter.png
    :align: center

As you can see, we have:

1. The action ``count`` that reads and writes the ``counter`` state field
2. The action ``done`` that reads the ``counter`` state field
3. A transition from ``count`` to ``count`` if ``counter < 10``
4. A transition from ``count`` to ``done`` otherwise

Finally, we can run the application:

.. code-block:: python

    app.run(until=["printer"])

If you want to copy/paste, you can open up the following code block and add to a file called ``run.py``:

.. collapse:: <code>run.py</code>

    .. code-block:: python

        from typing import Tuple

        from burr.core import (
            action,
            State,
            ApplicationBuilder,
            default,
            expr
        )


        @action(reads=["counter"], writes=["counter"])
        def count(state: State) -> Tuple[dict, State]:
            current = state["counter"] + 1
            result = {"counter": current}
            print("counted to ", current)
            return result, state.update(**result)  # return both the intermediate


        @action(reads=["counter"], writes=[])
        def done(state: State) -> Tuple[dict, State]:
            print("Bob's your uncle")
            return {}, state


        if __name__ == '__main__':
            app = (
                ApplicationBuilder()
                .with_state(counter=0)  # initialize the count to zero
                .with_actions(
                    count=count,  # add the counter action with the name "counter"
                    done=done  # add the printer action with the name "printer"
                ).with_transitions(
                    ("count", "count", expr("counter < 10")),  # Keep counting if the counter is less than 10
                    ("count", "done", default)  # Otherwise, we're done
                ).with_entrypoint("count")  # we have to start somewhere
                .build()
            )
            app.visualize("./graph", format="png", include_conditions=True, include_state=True)
            app.run(until=["printer"])


And the output looks exactly as we expect!

.. code-block:: text

    $ python run.py

    counted to 1
    counted to 2
    counted to 3
    counted to 4
    counted to 5
    counted to 6
    counted to 7
    counted to 8
    counted to 9
    counted to 10
    Bob's your uncle

All this to increment? Well, if all you want to do is count to 10, this might not be for you. But we imagine most of you want to do more exciting things
than count to 10...
