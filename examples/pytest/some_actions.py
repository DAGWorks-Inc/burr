# TODO: create some code to test

from typing import Any, Callable, Dict, Generator, List, Tuple

import openai

from burr import core
from burr.core import Action, ApplicationContext, GraphBuilder, State, action
from burr.core.parallelism import MapStates, RunnableGraph
from burr.tracking import LocalTrackingClient


@action(reads=["audio"], writes=["transcription"])
def transcribe_audio(state: State) -> State:
    # here we fake transcription. For this example the audio is text already...
    return state.update(transcription=state["audio"])


@action(reads=["hypothesis", "transcription"], writes=["diagnosis"])
def run_hypothesis(state: State) -> State:
    client = openai.Client()  # here for simplicity because clients and SERDE don't mix well.
    hypothesis = state["hypothesis"]
    transcription = state["transcription"]
    prompt = (
        f"Given the following diagnosis hypothesis and medical transcription:\n\n"
        f"Diagnosis hypothesis:{hypothesis}\n\n"
        f"Transcription:\n```{transcription}```\n\n"
        f"Answer 'yes' if you believe the hypothesis has a strong reason to hold given the content of the transcription."
        f"Answer 'no' if you do not believe the hypothesis holds given the content of the transcription."
        f"Answer 'unsure' if you are unsure and need more details."
    )
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a doctor diagnosing illnesses that is methodical"
                " in determining whether a diagnosis hypothesis is supported by a transcription.",
            },
            {"role": "user", "content": prompt},
        ],
        model="gpt-4o-mini",
    )
    return state.update(diagnosis=response.choices[0].message.content)


class TestMultipleHypotheses(MapStates):
    def action(self, state: State, inputs: Dict[str, Any]) -> Action | Callable | RunnableGraph:
        return run_hypothesis

    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        # You could easily have a list_hypotheses upstream action that writes to "hypothesis" in state
        # And loop through those
        # This hardcodes for simplicity
        for hypothesis in [
            "Common cold",
            "Sprained ankle",
            "Broken arm",
        ]:
            yield state.update(hypothesis=hypothesis)

    def reduce(self, state: State, states: Generator[State, None, None]) -> State:
        all_diagnoses_outputs = []
        for _sub_state in states:
            all_diagnoses_outputs.append(
                {"hypothesis": _sub_state["hypothesis"], "diagnosis": _sub_state["diagnosis"]}
            )
        return state.update(diagnosis_outputs=all_diagnoses_outputs)

    @property
    def reads(self) -> List[str]:
        return ["transcription"]

    @property
    def writes(self) -> List[str]:
        return ["diagnosis_outputs"]


@action(reads=["diagnosis_outputs"], writes=["final_diagnosis"])
def determine_diagnosis(state: State) -> State:
    # could also get an LLM to decide here, or have a human decide, etc.
    possible_hypotheses = [d for d in state["diagnosis_outputs"] if d["diagnosis"].lower() == "yes"]
    if len(possible_hypotheses) == 1:
        return state.update(final_diagnosis=possible_hypotheses[0]["hypothesis"])
    elif len(possible_hypotheses) > 1:
        return state.update(
            final_diagnosis="Need further clarification. Multiple diagnoses possible."
        )
    else:
        return state.update(final_diagnosis="Healthy individual")


def build_graph() -> core.Graph:
    graph = (
        GraphBuilder()
        .with_actions(
            transcribe_audio=transcribe_audio,
            hypotheses=TestMultipleHypotheses(),
            determine_diagnosis=determine_diagnosis,
        )
        .with_transitions(
            ("transcribe_audio", "hypotheses"),
            ("hypotheses", "determine_diagnosis"),
        )
        .build()
    )
    return graph


def build_application(
    app_id,
    graph,
    initial_state,
    initial_entrypoint,
    partition_key,
    tracker,
    use_otel_tracing: bool = False,
) -> core.Application:
    """Builds an application with the given parameters."""
    app_builder = (
        core.ApplicationBuilder()
        .with_graph(graph)
        .with_state(**initial_state)
        .with_entrypoint(initial_entrypoint)
        .with_identifiers(partition_key=partition_key, app_id=app_id)
    )
    if tracker:
        app_builder = app_builder.with_tracker(tracker, use_otel_tracing=use_otel_tracing)
    app = app_builder.build()
    return app


def run_my_agent(
    input_audio: str, partition_key: str = None, app_id: str = None, tracking_project: str = None
) -> Tuple[str, str]:
    graph = build_graph()
    tracker = None
    if tracking_project:
        tracker = LocalTrackingClient(project=tracking_project)
    # we fake the input audio to be a string here rather than a waveform.
    app = build_application(
        app_id, graph, {"audio": input_audio}, "transcribe_audio", partition_key, tracker=tracker
    )
    # app.visualize("diagnosis.png", include_conditions=True, view=False, format="png")
    last_action, _, agent_state = app.run(
        halt_after=["determine_diagnosis"],
        inputs={"audio": input_audio},
    )
    return input_audio, agent_state["final_diagnosis"]


if __name__ == "__main__":
    print(run_my_agent("Patient exhibits mucus dripping from nostrils and coughing."))
    print(run_my_agent("Patient has a limp and is unable to flex right ankle. Ankle is swollen."))
    print(
        run_my_agent(
            "Patient fell off and landed on their right arm. Their right wrist is swollen, they can still move their fingers, and there is only minor pain or discomfort when the wrist is moved or touched."
        )
    )
