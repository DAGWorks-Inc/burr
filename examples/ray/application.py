from typing import Any, Dict, List, Optional, Tuple

import openai
import ray

from burr.common.async_utils import SyncOrAsyncGenerator
from burr.core import Application, ApplicationBuilder, Condition, GraphBuilder, State, action
from burr.core.application import ApplicationContext
from burr.core.parallelism import MapStates, RunnableGraph, SubgraphType
from burr.core.persistence import SQLitePersister
from burr.integrations.ray import RayExecutor


# full agent
def _query_llm(prompt: str) -> str:
    """Simple wrapper around the OpenAI API."""
    client = openai.Client()
    return (
        client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
        )
        .choices[0]
        .message.content
    )


@action(
    reads=["feedback", "current_draft", "poem_type", "poem_subject"],
    writes=["current_draft", "draft_history", "num_drafts"],
)
def write(state: State) -> Tuple[dict, State]:
    """Writes a draft of a poem."""
    poem_subject = state["poem_subject"]
    poem_type = state["poem_type"]
    current_draft = state.get("current_draft")
    feedback = state.get("feedback")

    parts = [
        f'You are an AI poet. Create a {poem_type} poem on the following subject: "{poem_subject}". '
        "It is absolutely imperative that you respond with only the poem and no other text."
    ]

    if current_draft:
        parts.append(f'Here is the current draft of the poem: "{current_draft}".')

    if feedback:
        parts.append(f'Please incorporate the following feedback: "{feedback}".')

    parts.append(
        f"Ensure the poem is creative, adheres to the style of a {poem_type}, and improves upon the previous draft."
    )

    prompt = "\n".join(parts)

    draft = _query_llm(prompt)

    return {"draft": draft}, state.update(
        current_draft=draft,
        draft_history=state.get("draft_history", []) + [draft],
    ).increment(num_drafts=1)


@action(reads=["current_draft", "poem_type", "poem_subject"], writes=["feedback"])
def edit(state: State) -> Tuple[dict, State]:
    """Edits a draft of a poem, providing feedback"""
    poem_subject = state["poem_subject"]
    poem_type = state["poem_type"]
    current_draft = state["current_draft"]

    prompt = f"""
    You are an AI poetry critic. Review the following {poem_type} poem based on the subject: "{poem_subject}".
    Here is the current draft of the poem: "{current_draft}".
    Provide detailed feedback to improve the poem. If the poem is already excellent and needs no changes, simply respond with an empty string.
    """
    feedback = _query_llm(prompt)

    return {"feedback": feedback}, state.update(feedback=feedback)


@action(reads=["current_draft"], writes=["final_draft"])
def final_draft(state: State) -> Tuple[dict, State]:
    return {"final_draft": state["current_draft"]}, state.update(final_draft=state["current_draft"])


# full agent
@action(
    reads=[],
    writes=[
        "max_drafts",
        "poem_types",
        "poem_subject",
    ],
)
def user_input(state: State, max_drafts: int, poem_types: List[str], poem_subject: str) -> State:
    """Collects user input for the poem generation process."""
    return state.update(max_drafts=max_drafts, poem_types=poem_types, poem_subject=poem_subject)


class GenerateAllPoems(MapStates):
    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> SyncOrAsyncGenerator[State]:
        for poem_type in state["poem_types"]:
            yield state.update(current_draft=None, poem_type=poem_type, feedback=[], num_drafts=0)

    def action(self, state: State, inputs: Dict[str, Any]) -> SubgraphType:
        graph = (
            GraphBuilder()
            .with_actions(
                edit,
                write,
                final_draft,
            )
            .with_transitions(
                ("write", "edit", Condition.expr(f"num_drafts < {state['max_drafts']}")),
                ("write", "final_draft"),
                ("edit", "final_draft", Condition.expr("len(feedback) == 0")),
                ("edit", "write"),
            )
        ).build()
        return RunnableGraph(graph=graph, entrypoint="write", halt_after=["final_draft"])

    def reduce(self, state: State, results: SyncOrAsyncGenerator[State]) -> State:
        proposals = []
        for output_state in results:
            proposals.append(output_state["final_draft"])
        return state.append(proposals=proposals)

    @property
    def writes(self) -> list[str]:
        return ["proposals"]

    @property
    def reads(self) -> list[str]:
        return ["poem_types", "poem_subject", "max_drafts"]


@action(reads=["proposals", "poem_types"], writes=["final_results"])
def final_results(state: State) -> Tuple[dict, State]:
    # joins them into a string
    proposals = state["proposals"]
    final_results = "\n\n".join(
        [f"{poem_type}:\n{proposal}" for poem_type, proposal in zip(state["poem_types"], proposals)]
    )
    return {"final_results": final_results}, state.update(final_results=final_results)


def application_multithreaded() -> Application:
    app = (
        ApplicationBuilder()
        .with_actions(user_input, final_results, generate_all_poems=GenerateAllPoems())
        .with_transitions(
            ("user_input", "generate_all_poems"),
            ("generate_all_poems", "final_results"),
        )
        .with_tracker(project="demo:parallel_agents")
        .with_entrypoint("user_input")
        .build()
    )
    return app


def application(app_id: Optional[str] = None) -> Application:
    persister = SQLitePersister(db_path="./db")
    persister.initialize()
    app = (
        ApplicationBuilder()
        .with_actions(user_input, final_results, generate_all_poems=GenerateAllPoems())
        .with_transitions(
            ("user_input", "generate_all_poems"),
            ("generate_all_poems", "final_results"),
        )
        .with_tracker(project="demo:parallel_agents_fault_tolerance")
        .with_parallel_executor(RayExecutor)
        .with_state_persister(persister)
        .initialize_from(
            persister, resume_at_next_action=True, default_state={}, default_entrypoint="user_input"
        )
        .with_identifiers(app_id=app_id)
        .build()
    )
    return app


if __name__ == "__main__":
    ray.init()
    app = application()
    app_id = app.uid
    act, _, state = app.run(
        halt_after=["final_results"],
        inputs={
            "max_drafts": 2,
            "poem_types": [
                "sonnet",
                "limerick",
                "haiku",
                "acrostic",
            ],
            "poem_subject": "state machines",
        },
    )
    print(state)
