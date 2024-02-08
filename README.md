# Burr

## What is Burr?
Burr is a state machine for data/AI projects. You can (and should!) use it for anything where managing state can be hard. Hint: managing state
is always hard!

### Chatbot as a state machine

Let us take a look at of how one might design a gpt-like chatbot. It:
1. Accepts a prompt from the user
2. Does some simple checks/validations on that prompt (is it safe/within the terms of service)
3. If (2) it then decides the mode to which to respond to that prompt from a set of capabilities. Else respond accordingly.
   - generate an image
   - answer a question
   - write some code
   - ...
4. It then queries the appropriate model with the prompt, formatted as expected
5. If this fails, we present an error message
6. If this succeeds, we present the response to the user
7. Await a new prompt, GOTO (1)

Simple, right? Until you start tracking how state flows through:
- The prompt is referenced by multiple future steps
- The chat history is referred to at multiple points, and appended to (at (1) and (5))
- The decision on mode is opaque, and referred to both by (4), to know what model to query and by (6) to know how to render the response
- You will likely want to add more capabilities, more retries, etc...

Chatbots, while simple at first glance, turn into something of a beast when you want to bring them to production and understand exactly *why*
they make the decisions they do.

We can model this as a _State Machine_, using the following two concepts:
1. `Actions` -- a function that has two jobs. These form Nodes.
   - Compute some data given the state
   - Write back to the state with the data they compute
2. `Transitions` -- A pair of actions with a transition between them

The set of these together form what we will call a `Application` (effectively) a graph.

For those into the CS details, this is reverse to how a state machine is usually represented
(edges are normally actions and nodes are normally state). We've found this the easiest way to
express computation as simple python functions.

Let's look at a visual representation of our chatbot:
[<img src="demo_graph.png">](demo_graph.png)

You can see each node is an action, and each edge is a transition. Representing the state machine this way enables you to
break each action into a function of the state you need,
rationalize about the state changes of your system at any given point,
test any piece of the system with minimal effort, and add customizations
in to persist state, track state changes, and help you debug.

We built Burr to make all of that easy.


## Why the name Burr?

Burr is named after Aaron Burr, founding father, third VP of the United States, and murderer/arch-nemesis of Alexander Hamilton.
We imagine a world in which Burr and Hamilton lived in harmony and saw through their differences. We originally
built Burr as a _harness_ to handle state between executions of Hamilton DAGs,
but realized that it has a wide array of applications and decided to release it.

# Getting Started

Let's start with a simple example using the [cowsay](https://pypi.org/project/cowsay/) library.
We will go over installing burr, writing the code, running it, and
visualizing the state machine as we traverse through.

## Installing

First, install Burr:

```bash
pip install burr
```

## Cowsay

We're going to build something simple to simulate a talking cow. The cow will either say something, or not say something, depending on state.
To do this, we first define our actions. Note these are just python functions, and can leverage any python library/toolset you want!

```python
from burr.core import action, State
import random
import cowsay

@action(reads=[], writes=["cow_should_speak"])
def cow_should_speak(state: State) -> Tuple[dict, State]:
    result = {"cow_should_speak": random.randint(0, 3) == 0}
    return result, state.update(**result)

@action(reads=[], writes=["cow_said"])
def cow_say_hello(state: State) -> Tuple[dict, State]:
    says = cowsay.get_output_string(char="cow", text=say_what)
    result = {"cow_said": says}
    return result, state.update(**result)

@action(reads=[], writes=["cow_said"])
def cow_silent(state: State) -> Tuple[dict, State]:
    result = {"cow_said": "..."}
    return result, state.update(**result)
```

While these are simple python functions, they do have specific rules to them:
1. They must be decorated with `@action`, which specifies the reads and writes of the function
2. They must return a tuple of the result and the updated state. This is required to enable visibility into the results of each step and how the state changes.
3. They use the `State` API, which is a fancy immutable state mechanism to allow for efficient tracking/reproduction of state logic. It has multiple field-setting capabilities, but now you can just think of `.update(foo=bar)` as a function that returns a new state object with `foo` set to `bar`.

There is also a class-based API to allow for more complex state management/extensions, but we'll cover that later.

Now that we've defined the actions, let's define the transitions between them by building our application:


```python
from burr.core import ApplicationBuilder, when

application = (
    ApplicationBuilder()
    .with_actions(
        cow_should_speak=cow_should_speak,
        cow_says_nothing=cow_say.bind(say_what=None),
        cow_says_hello=cow_say.bind(say_what="Hello")
    ).with_transitions(
        ("cow_should_speak", "cow_say_hello", when(cow_should_speak=True)),
        ("cow_should_speak", "cow_say", when(cow_should_speak=False)),
        (["cow_say_hello", "cow_silent"], "cow_should_speak")
    ).build()
)
```

This has three actions:
1. `cow_should_speak` -- decides if the cow should speak
2. `cow_says_nothing` -- makes the cow say nothing
3. `cow_says_hello` -- makes the cow say hello

The transitions are conditional on value of `cow_should_speak` -- if it is true we move
from `cow_should_speak` to `cow_says_hello`, else we move to `cow_says_nothing`. The last
transition makes this a closed loop -- meaning we can run it forever (Burr can reprsent both infinite and finite state machines).
The condition is not specified, which indicates that it always evaluates to True. Conditions are evaluated in specified order.

Finally, let's run this. Just remember to eventually ctrl-c out of it, as it is an infinite loop.

```python
import time
while True:
    state, result, action = application.step()
    if action.name != "cow_should_speak":
        print(state["cow_said"]) # could also print result
    time.sleep(1)
```

And its as easy as that!
```bash
python cowsay_demo.py
...
  ___
| Sup |
  ===
   \
    \
      ^__^
      (oo)\_______
      (__)\       )\/\
          ||----w |
          ||     ||
...
```

## Running on streamlit

We have an example of running this on streamlit in the [examples directory](examples/cowsay).
The exciting part is that you can visualize the state machine as it runs, and see the state changes as they happen.
This is a powerful tool for debugging and understanding the state of your system at any given point, and can help
you answer the "why" behind any state change (and thus user output).

# Examples

See the following examples for more complex use-cases, otherwise keep reading for an overview of capabilities and APIs.
- [Cowsay](examples/cowsay) -- a simple example of a chatbot that can say something or not say something
- [Counter](examples/counter) -- a simple example of a counter that can count to 10
- [gpt](examples/gpt) -- the chatbot above
- [ml_training](examples/ml_training) -- a machine learning training pipeline
- [simulation](examples/simulation) -- a simulation of a trading system

# Capabilities

Burr has quite a few customization capabilities.

## Customization

### Hooks

We have a system of lifecycle adapters (adapted from [Hamilton's](https://github.com/dagworks-inc/hamilton) similar concept, which allow you to run tooling before and after
various places in a node's execution. For instance, you could (many of these are yet to be implemented):
1. Log every step as a trace in datadog
2. Add a time-delay to your steps to allow for rendering
3. Add a print statement to every step to see what happened (E.G. implement the printline in cowsay above)
4. Synchronize state/updates to an external database
5. Put results on a queue to feed to some monitoring system

And so on... Read more in the [hooks documentation](#hooks) below.

### Integrations

There are a few ways in which you can built custom integrations with Burr:

1. Custom actions that wrap your favorite library of capabilities (see Hamilton below), by extending the `Action` class. For instance:
    - (built) A Hamilton integration
    - (TODO) A Langchain integration
    - (TODO) An OpenAI integration
   Note that many of these are just syntactic sugar for wrapping in a python function.
2. Custom lifecycle hooks, by extending one of the lifecycle management classes (see above)
3. (TODO) Custom state management/persistence

## Current Capabilities

### Async

If an action defines an `async` run function, it will be automatically run asynchronously (under await).
Note that, while Burr does not allow for parallel walks of the state graph (see parallelism below), this can enable multiple actions
to run in parallel.

### Hamilton integration

Burr has first-class integrations for actions that form Hamilton DAGs. You can run any subset in Hamilton as a Burr action, using
the `burr.integrations.Hamilton` class. For example, the following will create a `Hamilton` action that runs a Hamilton DAG, wiring:

1. The `prompt_input` from the state value `prompt`
2. The `generated_image` to the state value `response`

```python
generate_image=Hamilton(
    inputs={"prompt_input": from_state("prompt")},
    outputs={"generated_image": update_state("response")},
)
```

Note that the inputs function as both inputs and overrides in Hamilton.

## Planned capabilities

### Parallelism

Burr does not allow for parallel walks, but it will have the notion of a "Multi-action". This is a single action
that wraps multiple, delegating to a threadpool or some customizable component. The results will stream in,
allowing a stream of state updates. This allows you to, say, run 10 jobs, aggregate the results, etc... Persistence
is then a matter of updating the state once jobs have been launched, and then updating the state again when they complete.
We will likely be building tooling that allows this to be automated to an extent, although we are still planning out that API.

### Langchain integration

TODO -- add simple LCEL example.

### (Planned) Typed State

We plan to add the ability to type-check state with some (or all) of the following:
- Pydantic
- dataclasses
- TypedDict
- Custom state schemas (through the `reads`/`writes` parameters)

The idea is you would define state at the function level, genericized by the state type, and Burr would be able to validate
against that state.

```python
class InputState(TypedDict):
    foo: int
    bar: str

class OutputState(TypedDict):
    baz: int
    qux: str

@action(reads=["foo", "bar"], writes=["baz"])
def my_action(state: State[InputState]) -> Tuple[dict, State[OutputState]]:
    result = {"baz": state["foo"] + 1, "qux": state["bar"] + "!"}
    return result, state.update(**result)
```

The above could also be dataclasses, pydantic models. We could also add something as simple as:

```python
@action(reads={"foo": int, "bar": str}, writes={"baz": int, "qux": str})
    ...
```

### (Planned) State Management/Immutability

We plan the ability to manage state in a few ways:
1. `commit` -- an internal tool to commit/compile a series of changes so that we have the latest state evaluated
2. `persist` -- a user-facing API to persist state to a database. This will be pluggable by the user, and we will have a few built-in
    options (e.g. a simple in-memory store, a file store, a database store, etc...)
3. `hydrate` -- a static method to hydrate state from a database. This will be pluggable by the user, and we will have a few built-in
    options that mirror those in `persist` options.

Currently state is immutable, but it utilizes an inefficient copy mechanism. This is out of expedience -- we don't anticipate this will
be painful for the time being, but plan to build a more efficient functional paradigm. We will likely have:
1. Each state object be a node in a linked list, with a pointer to the previous state. It carries a diff of the changes from the previous state.
2. An ability to `checkpoint` (allowing for state garbage collection), and store state in memory/kill out the pointers.

We will also consider having the ability to have a state solely backed by redis (and not memory), but we are still thinking through the API.

### (Planned) Compilation/Validation

We currently do not validate that the chain of actions provide a valid state, although we plan to walk the graph to ensure that no "impossible"
situation is reached. E.G. if an action reads from a state that is not written to (or not initialized), we will raise an error, likely upon calling `validate`.
We may be changing the behavior with defaults over time.

### (Planned) Exception Management

Currently, exceptions will break the control flow of an action, stopping the program early. Thus,
if an exception is expected, the program will stop early. We will be adding the ability to conditionally transition based
on exceptions, which will allow you to transition to an error-handling (or retry) action that does not
need the full outputs of the prior action.

Here is what it would look liek in the current API:

```python
@action(reads=["attempts"], writes=["output", "attempts"])
def some_flaky_action(state: State, max_retries: int=3) -> Tuple[dict, State]:
    result = {"output": None, "attempts": state["attempts"] + 1}
    try:
        result["output"] = call_some_api(...)
    excecpt APIException as e:
        if state["attempts"] >= max_retries:
           raise e
    return result, state.update(**result)
```

One could imagine adding it as a condition (a few possibilities)

```python
@action(reads=[], writes=["output"])
def some_flaky_action(state: State) -> Tuple[dict, State]:
    result = {"output": call_some_api(...)}
    return result, state.update(**result)

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
```

Will have to come up with ergonomic APIs -- the above are just some ideas.


### (Planned) Streaming results

TODO

# APIs

In lieu of a reference section/proper docs (coming soon), we'll go over the main APIs here. These are currently abridged,
and will reference out to the code for more instructions/docs.

## Class-based actions

### Custom

You can define an action by implementing the `Action` class:

```python
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
```

See [the code](burr/core/action.py) for more detail

### Result

If you just want to grab a result from the state, you can use the `Result` action:

```python
app = ApplicationBuilder().with_actions(
    get_result=Result(["var_from_state"])
)...
```

This simply grabs the value from the state and returns it as the result. It is purely a placeholder
for an action that should just use the result, although you do not need it.

## Conditions

Conditions have a few APIs, but the most common are the three convenience functions:

```python
from burr.core import when, expr, default
with_transitions(
    ("from", "to", when(foo="bar"),  # will evaluate when the state has the variable "foo" set to the value "bar"
    ("from", "to", expr('epochs>100')) # will evaluate to True when the state has the variable "foo" set to the value "bar"
    ("from", "to", default)  # will always evaluate to True
)
```

Conditions are evaluated in the order they are specified, and the first one that evaluates to True will be the transition that is selected
when determining which action to run next.

## State manipulation

State manipulation is done through the `State` class. The most common write are:

```python
state.update(foo=bar)  # update the state with the key "foo" set to "bar"
state.append(foo=bar)  # append "bar" to the list at "foo"
```

The read operations extend from those in the [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)
interface, but there are a few extra:

```python
state.subset(["foo", "bar"])  # return a new state with only the keys "foo" and "bar"
state.get_all()  # return a dictionary of all the state
```

When an update action is run, the state is first subsetted to get just the keys that are being read from,
then the action is run, and a new state is written to. This state is merged back into the original state
after the action is complete. Pseudocode:

```python
current_state = ...
read_state = current_state.subset(action.reads)
result = action.run(new_state)
write_state = current_state.subset(action.writes)
new_state = action.update(result, new_state)
current_state = current_state.merge(new_state)
```

If you're used to thinking about version control, this is a bit like a commit/checkout/merge mechanism.

## Binding parameters

Function-based actions can take in parameters which are akin to passing in constructor parameters. This is done through the `bind` method:

```python
@action(reads=[], writes=["cow_said"])
def cow_say_hello(state: State, say_what: str) -> Tuple[dict, State]:
    says = cowsay.get_output_string(char="cow", text=say_what)
    result = {"cow_said": says}
    return result, state.update(**result)

...with_action(cow_say_hello=cow_say_hello.bind(say_what="Hello"))
```

## Visualizing

You can visualize the application you built by calling the `visualize` method:

```python
application.visualize()
```
See docstring for more information. Note you have to have `burr[visualization]` installed to use this.

## Running

There are three APIs for executing an application. See the file [application.py](burr/core/application.py) for more information.

### `step`/`astep`

Returns the tuple of the action, the result of that action, and the new state. Call this if you want to run the application step-by-step.
```python
action, result, state = application.step()
```

If you're in an async context, you can run `astep` instead:

```python
action, result, state = await application.astep()
```

### `iterate`/`aiterate`

Iterate just runs `step` in a row, functioning as a generator:

```python
for action, result, state in application.iterate(until=["final_action_1", "final_action_2"]):
    print(action.name, result)
```

You can also run `aiterate` in an async context:

```python
async for action, result, state in application.aiterate():
    print(action.name, result)
```

In the synchronous context this also has a return value of a tuple of:
1. the final state
2. A list of the actions that were run, one for each result

You can access this by looking at the `value` variable of the `StopIteration` exception that is thrown
at the end of the loop, as is standard for python.
See the function implementation of `run` to show how this is done.

In the async context, this does not return anything
(asynchronous generators are not allowed a return value).

### `run`/`arun`

Run just calls out to `iterate` and returns the final state.

 ```python
 final_state, results = application.run(until=["final_action_1", "final_action_2"])
 ```

Currently the `until` variable is a `or` gate (E.G. `any_complete`), although we will be adding a `and` gate (E.G. `all_complete`).

## Lifecycle hooks

See the file [lifecycle.py](burr/core/lifecycle.py) for more information on the available hooks.
