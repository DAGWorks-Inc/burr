# Typed State

This example goes over how to use the typed state features in Burr with pydantic.

It will cover the following concepts:

1. Why you might want to use typing for your state in the first place
1. Define typing at the application level
1. Defining/altering state at the action level
1. Doing so in a streaming manner
1. Wiring that through to a FastAPI app

This README will contain snippets + link out to the code.

This adapts the [instructor + youtube example](../youtube-to-social-media-post/). This
takes in a youtube video, creates a transcript, and uses OpenAI to generate a social media post based on that transcript.

## Why type state?

Burr originally came without typing -- typing is an additional (optional) plugin that requires some complexity. So, why use typing at all? And why use Pydantic? Lots of good reasons:

### Typing provides guard-rails

Typing state ensures you have guarentees about what the data in your state is, and what shape it takes. This makes it easier to work with/manipulate.

### Typing makes development easier

IDEs have integrations for handling type annotations, enabling you to
avoid the cognitive burden of tracking types in your head. You get auto-completion on typed classes, and errors if you attempt to access or assign to a field that does not exist.

### Typing makes downstream integration easier

Multiple tools use types (especially with pydantic) to make interacting with data easier. In this example we use [instructor](https://python.useinstructor.com/blog/), as well as [FastAPI](https://fastapi.tiangolo.com/) to leverage pydantic models that Burr also uses.

### Typing provides a form of documentation

Type-annotation in python allows you to read your code and get some sense of what it is actually doing. This can be a warm introduction to python for those who came from the world of java initially (the authors of this library included), and make reasoning about a complex codebase simpler.

## Setting up your IDE

VSCode (or an editor with a similar interface) is generally optimal for this. It has
pluggable typing (e.g. pylance), which handles generics cleanly. Unfortunately pycharm
is often behind on typing support. See issues like [this](https://youtrack.jetbrains.com/issue/PY-44364) and [this](https://youtrack.jetbrains.com/issue/PY-27627/Support-explicitly-parametrized-generic-class-instantiation-syntax).

While it will still work in pycharm, you will not get some of the beter auto-completion capabilities.

## Defining typed state at the application level

This code for this is in [application.py](application.py).

First, define a pydantic model -- make it as recursive as you want. This will represent
your entire state. In this case, we're going to have a transcript of a youtube video that
was given by the user, as well as the social media post. The high-level is here -- the rest is
in the code:

```python
class ApplicationState(BaseModel):
    # Make these have defaults as they are only set in actions
    transcript: Optional[str] = Field(
        description="The full transcript of the YouTube video.", default=None
    )
    post: Optional[SocialMediaPost] = Field(
        description="The generated social media post.", default=None
    )
```

Note that this should exactly model your state -- we need to make things optional,
as there are points in the state where the transcript/post will not have been assigned.

Next, we add it in to the application object, both the initial value and the typing system.
The typing system is what's responsible for managing the schema:

```python
app = (
        ApplicationBuilder()
        .with_actions(
            ...
        )
        .with_transitions(
            ...
        )
        .with_entrypoint(...)
        .with_typing(PydanticTypingSystem(ApplicationState))
        .with_state(ApplicationState())
        .build()
    )
```

That ensures that application and the application's state object are parameterized on the state type.

To get the state, you can use `.data` on any state object returned by the application

```python
# just from the application
print(app.state.data.transcript)

# after execution
_, _, state = app.run(halt_after=..., inputs=...)
print(state.data.transcript)
```

## Defining/altering typed state at the action level

This code for this is in [application.py](application.py).

In addition to defining state centrally, we can define it at an action level.

The code is simple, but the API is slightly different from standard Burr. Rather than
using the immutable state-based API, we in-place mutate pydantic models. Don't worry, it's still immutable, you're just modifying a copy and returning it.

In this case, we call to `@action.pydantic`, which tells which fields to read/write to from state. It derives the classes from the function annotations, although you can also pass it the
pydantic classes as arguments to the decorator if you prefer.

Note that the reads/writes have to be a subset of the state object. In this case we use the global `ApplicationState` object as described above, although it can use a subset/compatible set of fields (or, if you elect not to use centralized state, it just has to be compatible with upstream/downstream versions).

Under the hood, burr will subset the state class so it only has the relevant fields (the reads/write) fields.

```python
@action.pydantic(reads=["transcript"], writes=["post"])
def generate_post(state: ApplicationState, llm_client) -> ApplicationState:
    """Use the Instructor LLM client to generate `SocialMediaPost` from the YouTube transcript."""

    # read the transcript from state
    transcript = state.transcript

    response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=SocialMediaPost,
        messages=[...]
    )
    # mutate in place
    state.post = response
    # return the state
    return state
```

## Typed state for streaming actions

This code for this is in [application.py](application.py).

For streaming actions, not only do we have to type the input/output state, but we can also type the intermediate result.

In this case, we just use the `SocialMediaPost` as we did in the application state. Instructor will be streaming that in as it gets created.

`@streaming_action.pydantic` currently requires you to pass in all the pydantic models as classes, although we will be adding the option to derive from the function signature.

We first call out to OpenAI, then we stream through

```python

@streaming_action.pydantic(
    reads=["transcript"],
    writes=["post"],
    state_input_type=ApplicationState,
    state_output_type=ApplicationState,
    stream_type=SocialMediaPost,
)
def generate_post_streaming(
    state: ApplicationState, llm_client
) -> Generator[Tuple[SocialMediaPost, Optional[ApplicationState]], None, None]:
    """Streams a post as it's getting created. This allows for interacting data on the UI side of partial
    results, using instructor's streaming capabilities for partial responses:
    https://python.useinstructor.com/concepts/partial/

    :param state: input state -- of the shape `ApplicationState`
    :param llm_client: the LLM client, we will bind this in the application
    :yield: a tuple of the post and the state -- state will be non-null when it's done
    """

    transcript = state.transcript
    response = llm_client.chat.completions.create_partial(
        model="gpt-4o-mini",
        response_model=SocialMediaPost,
        messages=[...],
        stream=True,
    )
    for post in response:
        yield post, None
    state.post = post
    yield post, state
```

When we call out to the application we built, we have to do a little magic to get typing to work
in the IDE, but we still have the same benefits as the non-streaming approach.

```python
app = build_streaming_application(...) # builder left out for now
_, streaming_container = app.stream_result(
    halt_after=["generate_post"],
    inputs={"youtube_url": "https://www.youtube.com/watch?v=hqutVJyd3TI"},
)
# annotate to make type-completion easier
streaming_container: StreamingResultContainer[ApplicationState, SocialMediaPost]
# post is of type SocialMediaPost
for post in streaming_container:
    obj = post.model_dump()
    console.clear()
    console.print(obj)
```

## FastAPI integration

This code for this is in [server.py](server.py).

To integrate this with FastAPI is easy, and gets easier with the types cascading through.

### Non-streaming

For the non-streaming case, we declare an endpoint that returns the entire state. Note you
may want a subset, but for now this is simple as it matches the pydantic models we defined above.

```python
@app.get("/social_media_post", response_model=SocialMediaPost)
def social_media_post(youtube_url: str = DEFAULT_YOUTUBE_URL) -> SocialMediaPost:
    _, _, state = burr_app.run(halt_after=["generate_post"], inputs={"youtube_url": youtube_url})
    return state.data.post
```

### Streaming

The streaming case involves using FastAPI's [StreamingResponse API](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse). We define a generator, which simply yields all
intermediate results:

```python

@app.get("/social_media_post_streaming", response_class=StreamingResponse)
def social_media_post_streaming(youtube_url: str = DEFAULT_YOUTUBE_URL) -> StreamingResponse:
    """Creates a completion for the chat message"""

    def gen():
        _, streaming_container = burr_app_streaming.stream_result(
            halt_after=["generate_post"],
            inputs={"youtube_url": youtube_url},
        )  # type: ignore
        for post in streaming_container:
            obj = post.model_dump()
            yield json.dumps(obj)

    return StreamingResponse(gen())
```

Note that `StreamingResponse` is not typed, but you have access to the types with the post
object, which corresponds to the stream from above!

Async streaming is similar.

You can run `server.py` with `python server.py`, which will open up on port 7443. You can use the `./curls.sh` command to query the server (it will use a default video, modify to pass your own):

```bash
./curls.sh # default, non-streaming
./curls.sh streaming #  streaming endpoint
./sucls.sh streaming_async # streaming async endpoint
```

Note you'll have to have [jq](https://jqlang.github.io/jq/) installed for this to work.

## Caveats + next steps

Some things we'll be building out shortly:

1. The ability to derive application level schemas from individual actions
2. The ability to automatically generate a FastAPI application from state + Burr
3. Configurable validation for state -- guardrails to choose when/when not to validate in pydantic
