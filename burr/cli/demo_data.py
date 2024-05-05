import importlib
import os

from application import logger

conversational_rag_application = importlib.import_module("examples.conversational-rag.application")
counter_application = importlib.import_module("examples.hello-world-counter.application")
chatbot_application = importlib.import_module("examples.multi-modal-chatbot.application")
chatbot_application_with_traces = importlib.import_module("examples.tracing-and-spans.application")


def generate_chatbot_data(data_dir: str, use_traces: bool):
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

    def _run_conversation(app_id, prompts):
        app = (chatbot_application_with_traces if use_traces else chatbot_application).application(
            app_id=app_id,
            storage_dir=data_dir,
        )
        for prompt in prompts:
            app.run(halt_after=["response"], inputs={"prompt": prompt})

    for app_id, prompts in sorted(working_conversations.items()):
        _run_conversation(app_id, prompts)
    old_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "fake"
    for app_id, prompts in sorted(broken_conversations.items()):
        try:
            _run_conversation(app_id, prompts)
        except Exception as e:
            print(f"Got an exception: {e}")
    os.environ["OPENAI_API_KEY"] = old_api_key


def generate_counter_data(data_dir: str = "~/.burr"):
    counts = [1, 10, 100, 50, 42]
    for i, count in enumerate(counts):
        app = counter_application.application(
            count_up_to=count,
            app_id=f"count-to-{count}",
            storage_dir=data_dir,
            partition_key=f"user_{i}",
        )
        app.run(halt_after=["result"])


def generate_rag_data(data_dir: str = "~/.burr"):
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
    for app_id, prompts in sorted(conversations.items()):
        app = conversational_rag_application.application(
            app_id=app_id,
            storage_dir=data_dir,
        )
        for prompt in prompts:
            app.run(halt_after=["ai_converse", "terminal"], inputs={"user_question": prompt})


def generate_all(data_dir: str):
    logger.info("Generating chatbot data")
    generate_chatbot_data(data_dir, False)
    logger.info("Generating chatbot data with traces")
    generate_chatbot_data(data_dir, True)
    logger.info("Generating counter data")
    generate_counter_data(data_dir)
    logger.info("Generating RAG data")
    generate_rag_data(data_dir)


#
