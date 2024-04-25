=================
Streaming Actions
=================

.. _streaming_actions:

.. note::

    Burr actions can stream results! This enables you to display results to the user as
    tokens are streamed in.

Actions can be implemented as streaming results. This enables a lower time-to-first-token and a more interactive
interface in the case of AI applications or streaming in of metrics in a model-training application. Broadly,
this is a tool to enable quicker user interaction in longer running actions that require user focus.

Streaming actions can be implemented as a class or a function, just like actions. However, they have a few additional rules:

#. They give intermediate results to the user as they are generated in the form of a generator
#. They are responsible for determining the relationship between the intermediate results and the final result
#. They have a ``return`` statement that handles result collection and state update

If you're not familiar with ``return`` statements in generators, you can read about them `here <https://www.python.org/dev/peps/pep-0380/>`_.
The high-level idea is that the ``return`` statement is used to raise a ``StopIteration`` exception with a value that is returned to the caller.
The framework uses this value to update the state of the action and to collect the final result.

A class-based streaming action might look like this:

.. code-block:: python

    from burr.core.action import StreamingAction

    class StreamingChatCall(StreamingAction):
        def stream_run(self, state: State, **run_kwargs) -> Generator[dict, None, dict]:
            client = openai.Client()
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{
                    'role': 'user',
                    'content': state["prompt"]
                }],
                temperature=0,
                stream=True,
            )
            buffer = []
            for chunk in response:
                delta = chunk.choices[0].delta.content
                buffer.append(delta)
                yield {'response': delta}
            full_response = ''.join(buffer)
            return {'response': full_response}

        @property
        def reads(self) -> list[str]:
            return ["prompt"]

        @property
        def writes(self) -> list[str]:
            return ["response"]

        def update(self, result: dict, state: State) -> State:
            return state.append(response=result["response"])

The logic is split between ``stream_run``, which is responsible for generating the intermediate results and
joining them into the final result, and update, which is responsible for collecting the final result and
updating the state. The ``return`` statement in ``stream_run`` is used to return the final result to the framework,
which is passed to ``update``.

The function-based equivalent would look very similar:

.. code-block:: python

    from burr.core.action import streaming_action

    @streaming_action(reads=["prompt"], writes=["prompt"])
    def streaming_chat_call(state: State, **run_kwargs) -> Generator[dict, None, Tuple[dict, State]]:
        client = openai.Client()
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{
                'role': 'user',
                'content': state["prompt"]
            }],
            temperature=0,
            stream=True,
        )
        buffer = []
        for chunk in response:
            delta = chunk.choices[0].delta.content
            buffer.append(delta)
            yield {'response': delta}
        full_response = ''.join(buffer)
        return {'response': full_response}, state.append(response=full_response)

As you can see above, we're doing the same thing, with a bit of syntactic sugar to combine the ``update`` and ``return`` statements.

Currently ``Async`` streaming actions are not supported. We will be adding shortly -- stay tuned! Follow the `issue on github <https://github.com/DAGWorks-Inc/burr/issues/64>`_ for more information.
