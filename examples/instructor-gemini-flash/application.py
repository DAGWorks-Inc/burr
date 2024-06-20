import time
from copy import deepcopy
from typing import Annotated

import google.generativeai as genai
import instructor
from dotenv import load_dotenv
from pydantic import AfterValidator, BaseModel, Field

from burr.core import Application, ApplicationBuilder, State, expr
from burr.core.action import action
from burr.tracking import LocalTrackingClient

load_dotenv()  # load the GOOGLE_API_KEY from your .env file

ask_gemini = instructor.from_gemini(
    client=genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
)

MIN_WORDS = 3
MAX_WORDS = 5
NUM_REQUIRED_TOPICS = 3
MIN_SUBTOPICS = 2
MAX_SUBTOPICS = 4
MIN_CONCEPTS = 2
MAX_CONCEPTS = 4
ATTEMPTS = 3
TEMPERATURE = 0.3


class Subtopic(BaseModel):
    name: Annotated[str, AfterValidator(str.title)]
    concepts: Annotated[
        list[str], AfterValidator(lambda concepts: [x.title() for x in concepts])
    ] = Field(
        description=f"{MIN_CONCEPTS}-{MAX_CONCEPTS} concepts covered in the subtopic.",
        min_length=MIN_CONCEPTS,
        max_length=MAX_CONCEPTS,
    )


class Topic(BaseModel):
    name: Annotated[str, AfterValidator(str.title)]
    subtopics: list[Subtopic] = Field(
        description=f"{MIN_SUBTOPICS}-{MAX_SUBTOPICS} ordered subtopics with concepts.",
        min_length=MIN_SUBTOPICS,
        max_length=MAX_SUBTOPICS,
    )

    def __str__(self) -> str:
        topic_str = f"TOPIC: {self.name}\n"
        for i, subtopic in enumerate(self.subtopics):
            topic_str += f"SUBTOPIC {i + 1}: {subtopic.name}\n"
            for j, concept in enumerate(subtopic.concepts):
                topic_str += f"CONCEPT {j + 1}: {concept}\n"
        return topic_str


def topics_system_template(
    num_required_topics: int = NUM_REQUIRED_TOPICS,
    min_words: int = MIN_WORDS,
    max_words: int = MAX_WORDS,
    min_subtopics: int = MIN_SUBTOPICS,
    max_subtopics: int = MAX_SUBTOPICS,
    min_concepts: int = MIN_CONCEPTS,
    max_concepts: int = MAX_CONCEPTS,
) -> str:
    return f"""\
"You are a world class course instructor."
You'll be given a course outline and you have to generate {num_required_topics} topics.
For each topic:
    1. Generate a {min_words}-{max_words} word topic name that encapsulates the description.
    2. Generate {min_subtopics}-{max_subtopics} subtopics for the topic. Also {min_words}-{max_words} words each.
    For each subtopic:
        Generate {min_concepts}-{max_concepts} concepts. Also {min_words}-{max_words} words each. The concepts should be related to the subtopic.
        Think of concepts as the smallest unit of knowledge that can be taught from the subtopic. And add a verb to the concept to make it actionable.
        For example:
            "Calculate Derivatives" instead of "Derivatives".
            "Identify Finite Sets" instead of "Finite Sets".
            "Find the y-intercept" instead of "y-intercept".
    The subtopics and concepts should be in the correct order.\
"""


def creation_template(
    outline: str,
    topics_so_far: list[Topic],
    num_required_topics: int = NUM_REQUIRED_TOPICS,
) -> str:
    prompt_strs = [
        f"<outline>\n{outline}\n</outline>",
        f"<num_required_topics>\n{num_required_topics}\n</num_required_topics>",
    ]
    topics_so_far_str = "<topics_so_far>\n"
    if topics_so_far:
        for i, topic in enumerate(topics_so_far):
            topics_so_far_str += f"{i+1}/{num_required_topics}\n{topic}\n"
    topics_so_far_str = topics_so_far_str.strip() + "\n</topics_so_far>"
    prompt_strs.append(topics_so_far_str)
    prompt_strs.append("Generate the next topic.")
    return "\n\n".join(prompt_strs)


@action(reads=[], writes=["outline", "num_required_topics", "chat_history"])
def setup(state: State, outline: str, num_required_topics: int) -> State:
    return state.update(
        outline=outline,
        num_required_topics=num_required_topics,
        chat_history=[
            {
                "role": "system",
                "content": topics_system_template(num_required_topics=num_required_topics),
            }
        ],
    )


@action(
    reads=[
        "chat_history",
        "outline",
        "num_required_topics",
        "topics_so_far",
        "topic_feedback",
    ],
    writes=["generated_topic", "chat_history"],
)
def creator(
    state: State,
    attempts: int = ATTEMPTS,
) -> tuple[dict, State]:
    """
    Generates a topic based on the outline and topics generated so far using the create function from the Instructor library.
    https://python.useinstructor.com/#using-gemini

    Parameters:
    - state (State): The current state of the application.
    - attempts (int, optional): The number of times the model should try to generate a response. 3 by default. If the model fails to generate a response after the specified number of attempts, the function will return with 'generated_topic' set to None.

    Returns:
    - tuple[dict, State]: A tuple containing the generated topic and the updated state.

    Instructor Parameters Used:
    - response_model: The Pydantic model or the type that we want the response to be. In our case, it's the `Topic` model.
    - messages: The chat history that we want to pass to the model. This could have the prompt for generating the next topic, or the previously generated topic with user feedback.
    - max_retries: The number of times we want to retry if the model fails to generate a response. 1 means just the original attempt, 2 means the original attempt and one retry.
    - temperature: The temperature of the model. A float between 0 and 1. Lower values give more deterministic results. 0.3 by default.
    """

    num_required_topics = state.get("num_required_topics", NUM_REQUIRED_TOPICS)
    topics_so_far = state.get("topics_so_far", [])
    topic_feedback = state.get("topic_feedback", "")
    messages = deepcopy(state["chat_history"])
    if topic_feedback:
        user_message = f"User feedback: {topic_feedback.strip()}"
    else:
        user_message = creation_template(
            outline=state["outline"],
            topics_so_far=topics_so_far,
            num_required_topics=num_required_topics,
        )
    messages.append({"role": "user", "content": user_message})
    create_kwargs = dict(
        response_model=Topic,
        messages=messages,
        max_retries=attempts,
        temperature=TEMPERATURE,
    )
    try:
        res = ask_gemini.create(**create_kwargs)  # type: ignore
    except Exception as e:
        print(f"ERROR in creator: {e}")
        return {"generated_topic": None}, state.update(generated_topic="")
    return {"generated_topic": res}, state.update(generated_topic=res).append(
        chat_history={"role": "user", "content": user_message}
    ).append(chat_history={"role": "assistant", "content": str(res)})


@action(
    reads=["generated_topic", "num_required_topics", "topics_so_far"],
    writes=["topic_feedback"],
)
def get_topic_feedback(state: State) -> tuple[dict, State]:
    time.sleep(2)
    num_required_topics = state.get("num_required_topics", NUM_REQUIRED_TOPICS)
    num_topics_so_far = len(state.get("topics_so_far", []))
    generated_topic = state["generated_topic"]
    generated_topic_str = f"{num_topics_so_far+1}/{num_required_topics}\n{generated_topic}"
    feedback = (
        input(
            f"Give your feedback on this generated topic. Leave empty if it's perfect.\n\n{generated_topic_str}"
        )
        or None
    )

    return {"topic_feedback": feedback}, state.update(topic_feedback=feedback)


@action(reads=["generated_topic"], writes=["topics_so_far"])
def update_topics_so_far(state: State) -> State:
    return state.append(topics_so_far=state["generated_topic"])


@action(reads=["topics_so_far"], writes=[])
def terminal(state: State) -> tuple[dict, State]:
    return {"topics_so_far": state["topics_so_far"]}, state


def application(
    app_id: str | None = None,
    username: str | None = None,
    project: str = "topics_creator",
) -> Application:
    tracker = LocalTrackingClient(project=project)
    builder = (
        ApplicationBuilder()
        .with_actions(setup, creator, get_topic_feedback, update_topics_so_far, terminal)
        .with_transitions(
            ("setup", "creator"),
            ("creator", "creator", expr("generated_topic is None")),  # type: ignore
            ("creator", "get_topic_feedback"),
            (
                "get_topic_feedback",
                "update_topics_so_far",
                expr("topic_feedback is None"),  # type: ignore
            ),
            ("get_topic_feedback", "creator"),
            (
                "update_topics_so_far",
                "terminal",
                expr("len(topics_so_far) == num_required_topics"),  # type: ignore
            ),
            ("update_topics_so_far", "creator"),
        )
        .with_tracker("local", project=project)
        .with_identifiers(app_id=app_id, partition_key=username)  # type: ignore
        .initialize_from(
            tracker,
            resume_at_next_action=True,
            default_entrypoint="setup",
            default_state={},
        )
    )
    return builder.build()


if __name__ == "__main__":
    app = application()
    app.visualize(
        output_file_path="statemachine",
        include_conditions=True,
        include_state=True,
        format="png",
    )
