from hamilton.driver import Builder, Driver

from burr.core import ApplicationBuilder, State, action


@action(reads=[], writes=[])
def ingest_blog(state: State, blog_post_url: str, dr: Driver) -> State:
    """Download a blog post and parse it"""
    dr.execute(["embed_chunks"], inputs={"blog_post_url": blog_post_url})
    return state


@action(reads=[], writes=["llm_answer"])
def ask_question(state: State, user_query: str, dr: Driver) -> State:
    """Reply to the user's query using the blog's content."""
    results = dr.execute(["llm_answer"], inputs={"user_query": user_query})
    return state.update(llm_answer=results["llm_answer"])


if __name__ == "__main__":
    # renames to avoid name conflicts with the @action functions
    from actions import ask_question as ask_module
    from actions import ingest_blog as ingest_module
    from hamilton.plugins.h_opentelemetry import OpenTelemetryTracer
    from opentelemetry.instrumentation.lancedb import LanceInstrumentor
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    OpenAIInstrumentor().instrument()
    LanceInstrumentor().instrument()

    dr = (
        Builder()
        .with_modules(ingest_module, ask_module)
        .with_adapters(OpenTelemetryTracer())
        .build()
    )

    app = (
        ApplicationBuilder()
        .with_actions(ingest_blog.bind(dr=dr), ask_question.bind(dr=dr))
        .with_transitions(("ingest_blog", "ask_question"))
        .with_entrypoint("ingest_blog")
        .with_tracker(project="modular-rag", use_otel_tracing=True)
        .build()
    )

    action_name, results, state = app.run(
        halt_after=["ask_question"],
        inputs={
            "blog_post_url": "https://blog.dagworks.io/p/from-blog-to-bot-build-a-rag-app",
            "user_query": "What do you need to monitor in a RAG app?",
        },
    )
    print(state["llm_answer"])
