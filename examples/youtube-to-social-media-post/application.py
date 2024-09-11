import textwrap
from typing import Any, AsyncGenerator, Generator, Optional, Tuple, Union

import instructor
import openai
from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema
from rich.console import Console
from youtube_transcript_api import YouTubeTranscriptApi

from burr.core import Application, ApplicationBuilder, action
from burr.core.action import (
    AsyncStreamingResultContainer,
    StreamingResultContainer,
    streaming_action,
)
from burr.integrations.pydantic import PydanticTypingSystem


class Concept(BaseModel):
    term: str = Field(description="A key term or concept mentioned.")
    definition: str = Field(description="A brief definition or explanation of the term.")
    timestamp: float = Field(description="Timestamp when the concept is explained.")

    def display(self):
        minutes, seconds = divmod(self.timestamp, 60)
        return f"{int(minutes)}:{int(seconds)} - {self.term}: {self.definition}"


class SocialMediaPost(BaseModel):
    """A social media post about a YouTube video generated its transcript"""

    topic: str = Field(description="Main topic discussed.")
    hook: str = Field(
        description="Statement to grab the attention of the reader and announce the topic."
    )
    body: str = Field(
        description="The body of the social media post. It should be informative and make the reader curious about viewing the video."
    )
    concepts: list[Concept] = Field(
        description="Important concepts about Hamilton or Burr mentioned in this post -- please have at least 1",
        min_items=0,
        max_items=3,
        validate_default=False,
    )
    key_takeaways: list[str] = Field(
        description="A list of informative key takeways for the reader -- please have at least 1",
        min_items=0,
        max_items=4,
        validate_default=False,
    )
    youtube_url: SkipJsonSchema[Union[str, None]] = None

    def display(self) -> str:
        formatted_takeways = " ".join([t for t in self.key_takeaways])
        formatted_concepts = "CONCEPTS\n" + "\n".join([c.display() for c in self.concepts])
        link = f"link: {self.youtube_url}\n\n" if self.youtube_url else ""

        return (
            textwrap.dedent(
                f"""\
            TOPIC: {self.topic}

            {self.hook}

            {self.body}

            {formatted_takeways}

            """
            )
            + link
            + formatted_concepts
        )


class ApplicationState(BaseModel):
    # Make these have defaults as they are only set in actions
    transcript: Optional[str] = Field(
        description="The full transcript of the YouTube video.", default=None
    )
    post: Optional[SocialMediaPost] = Field(
        description="The generated social media post.", default=None
    )


class ApplicationStateStream(ApplicationState):
    # Make these have defaults as they are only set in actions
    post_generator: Optional[Generator[SocialMediaPost, None, None]] = None

    class Config:
        arbitrary_types_allowed = True

    def __copy__(self, memo: dict[int, Any] | None = None):
        post_generator = self.post_generator
        self.post_generator = None
        out = self.model_copy(deep=True, update={"post_generator": post_generator})
        self.post_generator = post_generator
        return out
        # # TODO -- ensure that post_generator is copied by reference, not value...
        # # Ignore this for now -- this is specifically dealing with a copy() issue
        # # then delegate to the superclass
        # if memo is None:
        #     memo = {}
        # if id(self) in memo:
        #     return memo[id(self)]

        # # Create a shallow copy to modify
        # new_obj = copy.copy(self)

        # # Copy each attribute except the generator which should be shared
        # for k, v in self.__dict__.items():
        #     if k != "post_generator":
        #         setattr(new_obj, k, copy.deepcopy(v, memo))

        # # Reference the same generator instance
        # new_obj.post_generator = self.post_generator

        # # Store in memoization dictionary
        # memo[id(self)] = new_obj

        # return new_obj


@action.pydantic(reads=[], writes=["transcript"])
def get_youtube_transcript(state: ApplicationState, youtube_url: str) -> ApplicationState:
    """Get the official YouTube transcript for a video given it's URL"""
    _, _, video_id = youtube_url.partition("?v=")

    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    state.transcript = " ".join([f"ts={entry['start']} - {entry['text']}" for entry in transcript])
    return state

    # store the transcript in state


@action.pydantic(reads=["transcript"], writes=["post"])
def generate_post(state: ApplicationState, llm_client) -> ApplicationState:
    """Use the Instructor LLM client to generate `SocialMediaPost` from the YouTube transcript."""

    # read the transcript from state
    transcript = state.transcript

    response = llm_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=SocialMediaPost,
        messages=[
            {
                "role": "system",
                "content": "Analyze the given YouTube transcript and generate a compelling social media post.",
            },
            {"role": "user", "content": transcript},
        ],
    )
    state.post = response

    # store the chapters in state
    return state


@streaming_action.pydantic(
    reads=["transcript"],
    writes=["post"],
    state_input_type=ApplicationState,
    state_output_type=ApplicationState,
    stream_type=SocialMediaPost,
)
def generate_post_streaming(
    state: ApplicationStateStream, llm_client
) -> Generator[Tuple[SocialMediaPost, Optional[ApplicationState]], None, None]:
    """Use the Instructor LLM client to generate `SocialMediaPost` from the YouTube transcript."""

    transcript = state.transcript
    response = llm_client.chat.completions.create_partial(
        model="gpt-4o-mini",
        response_model=SocialMediaPost,
        messages=[
            {
                "role": "system",
                "content": "Analyze the given YouTube transcript and generate a compelling social media post.",
            },
            {"role": "user", "content": transcript},
        ],
        stream=True,
    )
    final_post = None
    for post in response:
        final_post = post
        yield post, None

    yield final_post, state


@streaming_action.pydantic(
    reads=["transcript"],
    writes=["post"],
    state_input_type=ApplicationState,
    state_output_type=ApplicationState,
    stream_type=SocialMediaPost,
)
async def generate_post_streaming_async(
    state: ApplicationStateStream, llm_client
) -> AsyncGenerator[Tuple[SocialMediaPost, Optional[ApplicationState]], None]:
    """Use the Instructor LLM client to generate `SocialMediaPost` from the YouTube transcript."""

    transcript = state.transcript
    response = llm_client.chat.completions.create_partial(
        model="gpt-4o-mini",
        response_model=SocialMediaPost,
        messages=[
            {
                "role": "system",
                "content": "Analyze the given YouTube transcript and generate a compelling social media post.",
            },
            {"role": "user", "content": transcript},
        ],
        stream=True,
    )
    final_post = None
    async for post in response:
        final_post = post
        yield post, None

    yield final_post, state


def build_application() -> Application[ApplicationState]:
    llm_client = instructor.from_openai(openai.OpenAI())
    app = (
        ApplicationBuilder()
        .with_actions(
            get_youtube_transcript,
            generate_post.bind(llm_client=llm_client),
        )
        .with_transitions(
            ("get_youtube_transcript", "generate_post"),
            ("generate_post", "get_youtube_transcript"),
        )
        # .with_state_persister(SQLLitePersister(db_path=".burr.db", table_name="state"))
        .with_entrypoint("get_youtube_transcript")
        .with_typing(PydanticTypingSystem(ApplicationState))
        .with_state(ApplicationState())
        .with_tracker(project="youtube-post")
        .build()
    )
    return app


def build_streaming_application() -> Application[ApplicationState]:
    llm_client = instructor.from_openai(openai.OpenAI())
    app = (
        ApplicationBuilder()
        .with_actions(
            get_youtube_transcript,
            generate_post=generate_post_streaming.bind(llm_client=llm_client),
        )
        .with_transitions(
            ("get_youtube_transcript", "generate_post"),
            ("generate_post", "get_youtube_transcript"),
        )
        # .with_state_persister(SQLLitePersister(db_path=".burr.db", table_name="state"))
        .with_entrypoint("get_youtube_transcript")
        .with_typing(PydanticTypingSystem(ApplicationState))
        .with_state(ApplicationState())
        .with_tracker(project="youtube-post")
        .build()
    )
    return app


def build_streaming_application_async() -> Application[ApplicationState]:
    llm_client = instructor.from_openai(openai.AsyncOpenAI())
    app = (
        ApplicationBuilder()
        .with_actions(
            get_youtube_transcript,
            generate_post=generate_post_streaming_async.bind(llm_client=llm_client),
        )
        .with_transitions(
            ("get_youtube_transcript", "generate_post"),
            ("generate_post", "get_youtube_transcript"),
        )
        # .with_state_persister(SQLLitePersister(db_path=".burr.db", table_name="state"))
        .with_entrypoint("get_youtube_transcript")
        .with_typing(PydanticTypingSystem(ApplicationState))
        .with_state(ApplicationState())
        .with_tracker(project="test-youtube-post")
        .build()
    )
    return app


async def run_async():
    console = Console()
    app = build_streaming_application_async()

    a, streaming_container = await app.astream_result(
        halt_after=["generate_post"],
        inputs={"youtube_url": "https://www.youtube.com/watch?v=hqutVJyd3TI"},
    )  # type: ignore
    streaming_container: AsyncStreamingResultContainer[ApplicationState, SocialMediaPost]

    async for post in streaming_container:
        obj = post.model_dump()
        console.clear()
        console.print(obj)


if __name__ == "__main__":
    console = Console()
    app = build_streaming_application()
    a, streaming_container = app.stream_result(
        halt_after=["generate_post"],
        inputs={"youtube_url": "https://www.youtube.com/watch?v=hqutVJyd3TI"},
    )  # type: ignore
    streaming_container: StreamingResultContainer[ApplicationState, SocialMediaPost]
    for post in streaming_container:
        obj = post.model_dump()
        console.clear()
        console.print(obj)
