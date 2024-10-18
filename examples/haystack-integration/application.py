import os

from haystack.components.builders import PromptBuilder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from burr.core import ApplicationBuilder, State, action
from burr.integrations.haystack import HaystackAction

# dummy OpenAI key to avoid raising an error
os.environ["OPENAI_API_KEY"] = "sk-..."


embed_text = HaystackAction(
    component=SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"),
    name="embed_text",
    reads=[],
    writes={"embedding": "query_embedding"},
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
    writes={"prompt": "question_prompt"},
)


generate_answer = HaystackAction(
    component=OpenAIGenerator(model="gpt-4o-mini"),
    name="generate_answer",
    reads={"question_prompt": "prompt"},
    writes={"text": "answer"},
)


@action(reads=["answer"], writes=[])
def display_answer(state: State) -> State:
    print(state["answer"])
    return state


def build_application():
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
    app = build_application()
    app.visualize(include_state=True)
