import importlib
import logging
import os
import uuid
from typing import Optional

from burr.core import ApplicationBuilder, Result, default, expr
from burr.core.graph import GraphBuilder
from burr.tracking import LocalTrackingClient
from burr.tracking.s3client import S3TrackingClient

logger = logging.getLogger(__name__)

conversational_rag_application = importlib.import_module(
    "examples.conversational-rag.simple_example.application"
)
counter_application = importlib.import_module("examples.hello-world-counter.application")
chatbot_application = importlib.import_module("examples.multi-modal-chatbot.application")
chatbot_application_with_traces = importlib.import_module("examples.tracing-and-spans.application")


def generate_chatbot_data(
    data_dir: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    use_traces: bool = False,
    unique_app_names: bool = False,
):
    project_id = "demo_chatbot" if not use_traces else "demo_chatbot_with_traces"
    run_prefix = str(uuid.uuid4())[0:8] + "-" if unique_app_names else ""
    working_conversations = {
        "chat-1-giraffe": [
            "Please draw a giraffe.",  # Answered by the image mode
            "Please write a function that queries the internet for the height of a giraffe",  # answered by the code mode
            "OK, just tell me, how tall is a giraffe?",  # answered by the question mode
            "Please build me a giraffe",  # Answered by nothing
            "If Aaron burr were an animal, would he be a giraffe?",  # answered by the question mode
        ],
        "chat-2-geography": [
            "What is the capital of France?",  # answered by the question mode
            "Please draw a map of the world",  # answered by the image mode
            "Please write code to compute the circumpherence of the earth",  # answered by the code mode
            "Geography! Geography! Geography!",  # answered by nothing
        ],
        "chat-3-physics": [
            "Please draw a free-body diagram of a block on a ramp",  # answered by the image mode
            "Please write code to compute the force of gravity on the moon",  # answered by the code mode
            "What is the force of gravity on the moon?",  # answered by the question mode
            "Please build me a block on a ramp",  # answered by nothing
        ],
        "chat-4-philosophy": [
            "Please draw a picture of a philosopher",  # answered by the image mode
            "Please write code to compute the meaning of life (hint, its 42)",  # answered by the code mode
            "What is the meaning of life?",  # answered by the question mode (ish)
        ],
        "chat-5-jokes": [
            "Please draw a picture of a good joke",  # answered by the image mode
            "Please write code for an interactive knock-knock joke",  # answered by the code mode
            "What is a good joke?",  # answered by the question mode
            "The chicken crossed the road because it was a free-range chicken",  # answered by nothing
        ],
    }
    broken_conversations = {"chat-6-demonstrate-errors": working_conversations["chat-1-giraffe"]}

    def _modify(app_id: str) -> str:
        return run_prefix + app_id

    def _run_conversation(app_id, prompts):
        tracker = (
            LocalTrackingClient(project=project_id + "_otel", storage_dir=data_dir)
            if not s3_bucket
            else S3TrackingClient(project=project_id, bucket=s3_bucket)
        )
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor

        # TODO -- get this auto-registered
        OpenAIInstrumentor().instrument()
        graph = (chatbot_application_with_traces if use_traces else chatbot_application).graph
        app = (
            ApplicationBuilder()
            .with_graph(graph)
            .with_identifiers(app_id=app_id)
            .with_tracker(tracker, use_otel_tracing=True)
            .with_entrypoint("prompt")
            .build()
        )
        for prompt in prompts:
            app.run(halt_after=["response"], inputs={"prompt": prompt})

    for app_id, prompts in sorted(working_conversations.items()):
        _run_conversation(_modify(app_id), prompts)
    old_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "fake"
    for app_id, prompts in sorted(broken_conversations.items()):
        try:
            _run_conversation(_modify(app_id), prompts)
        except Exception as e:
            print(f"Got an exception: {e}")
    os.environ["OPENAI_API_KEY"] = old_api_key


def generate_counter_data(
    data_dir: str = "~/.burr", s3_bucket: Optional[str] = None, unique_app_names: bool = False
):
    counter = counter_application.counter
    tracker = (
        LocalTrackingClient(project="demo_counter", storage_dir=data_dir)
        if not s3_bucket
        else S3TrackingClient(project="demo_counter", bucket=s3_bucket)
    )

    counts = [1, 10, 100, 50, 42]
    # This is just cause we don't want to change the code
    # TODO -- add ability to grab graph from application or something like that
    graph = (
        GraphBuilder()
        .with_actions(counter=counter, result=Result("counter"))
        .with_transitions(
            ("counter", "counter", expr("counter < count_to")),
            ("counter", "result", default),
        )
        .build()
    )
    for i, count in enumerate(counts):
        app_id = f"count-to-{count}"
        if unique_app_names:
            suffix = str(uuid.uuid4())[0:8]
            app_id = f"{app_id}-{suffix}"
        app = (
            ApplicationBuilder()
            .with_graph(graph)
            .with_identifiers(app_id=app_id, partition_key=f"user_{i}")
            .with_state(count_to=count, counter=0)
            .with_tracker(tracker)
            .with_entrypoint("counter")
            .build()
        )
        app.run(halt_after=["result"])


def generate_rag_data(
    data_dir: Optional[str] = None, s3_bucket: Optional[str] = None, unique_app_names: bool = False
):
    conversations = {
        "rag-1-food": [
            "What is Elijah's favorite food?",
            "What is Stefan's favorite food?",
            "What is Aaron's favorite food?",  # unknown
            "exit",
        ],
        "rag-2-work-history": [
            "Where did Elijah work?",
            "Where did Stefan work?",
            "Where did Harrison work?",
            "Where did Jonathan work?",
            "Did Stefan and Harrison work together?",
            "exit",
        ],
        "rag-3-activities": [
            "What does Elijah like to do?",
            "What does Stefan like to do?",
            "exit",
        ],
        "rag-4-everything": [
            "What is Elijah's favorite food?",
            "Where did Elijah work?",
            "Where did Stefan work" "What does Elijah like to do?",
            "What is Stefan's favorite food?",
            "Whose favorite food is better, Elijah's or Stefan's?" "exit",
        ],
    }
    prefix = str(uuid.uuid4())[0:8] + "-" if unique_app_names else ""
    for app_id, prompts in sorted(conversations.items()):
        graph = conversational_rag_application.graph()
        tracker = (
            LocalTrackingClient(project="demo_conversational-rag", storage_dir=data_dir)
            if not s3_bucket
            else S3TrackingClient(project="demo_conversational-rag", bucket=s3_bucket)
        )
        app_id = f"{prefix}{app_id}" if unique_app_names else app_id
        app = (
            ApplicationBuilder()
            .with_graph(graph)
            .with_identifiers(app_id=app_id)
            .with_tracker(tracker)
            .with_entrypoint("human_converse")
            .build()
        )
        logger.warning(f"Running {app_id}...")
        for prompt in prompts:
            app.run(halt_after=["ai_converse", "terminal"], inputs={"user_question": prompt})


def generate_all(
    data_dir: Optional[str] = None, s3_bucket: Optional[str] = None, unique_app_names: bool = False
):
    logger.info("Generating chatbot data")
    generate_chatbot_data(
        data_dir=data_dir, s3_bucket=s3_bucket, use_traces=False, unique_app_names=unique_app_names
    )
    logger.info("Generating chatbot data with traces")
    generate_chatbot_data(
        data_dir=data_dir, s3_bucket=s3_bucket, use_traces=True, unique_app_names=unique_app_names
    )
    logger.info("Generating counter data")
    generate_counter_data(data_dir=data_dir, s3_bucket=s3_bucket, unique_app_names=unique_app_names)
    logger.info("Generating RAG data")
    generate_rag_data(data_dir=data_dir, s3_bucket=s3_bucket, unique_app_names=unique_app_names)
