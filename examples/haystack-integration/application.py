from haystack.components.builders import PromptBuilder
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from burr.core import ApplicationBuilder, State, action
from burr.integrations.haystack import HaystackAction


@action(reads=["answer"], writes=[])
def display_answer(state: State) -> State:
    print(state["answer"])
    return state


def build_application():
    embed_text = HaystackAction(
        component=OpenAITextEmbedder(model="text-embedding-3-small"),
        name="embed_text",
        reads=[],
        writes={"query_embedding": "embedding"},
    )

    retrieve_documents = HaystackAction(
        component=InMemoryEmbeddingRetriever(InMemoryDocumentStore()),
        name="retrieve_documents",
        reads=["query_embedding"],
        writes=["documents"],
    )

    build_prompt = HaystackAction(
        component=PromptBuilder(template="Document: {{documents}} Question: {{question}}"),
        name="build_prompt",
        reads=["documents"],
        writes={"question_prompt": "prompt"},
    )

    generate_answer = HaystackAction(
        component=OpenAIGenerator(model="gpt-4o-mini"),
        name="generate_answer",
        reads={"prompt": "question_prompt"},
        writes={"answer": "replies"},
    )

    return (
        ApplicationBuilder()
        .with_actions(
            embed_text,
            retrieve_documents,
            build_prompt,
            generate_answer,
            display_answer,
        )
        .with_transitions(
            ("embed_text", "retrieve_documents"),
            ("retrieve_documents", "build_prompt"),
            ("build_prompt", "generate_answer"),
            ("generate_answer", "display_answer"),
        )
        .with_entrypoint("embed_text")
        .build()
    )


if __name__ == "__main__":
    import os

    os.environ["OPENAI_API_KEY"] = "sk-..."

    app = build_application()

    _, _, state = app.run(
        halt_after=["display_answer"],
        inputs={
            "text": "What is the capital of France?",
            "question": "What is the capital of France?",
        },
    )
    app.visualize(include_state=True)
