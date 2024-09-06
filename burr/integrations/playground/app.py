import litellm
import streamlit as st

from burr.core import Application, ApplicationBuilder, State, action
from burr.integrations.streamlit import (
    application_selectbox,
    get_steps,
    project_selectbox,
    step_selectbox,
)
from burr.tracking import LocalTrackingClient
from burr.tracking.server.backend import LocalBackend
from burr.visibility import TracerFactory


@st.cache_data
def instrument(provider: str):
    msg = None
    if provider == "openai":
        try:
            from opentelemetry.instrumentation.openai import (  # openai is a dependency of litellm
                OpenAIInstrumentor,
            )

            OpenAIInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "cohere":
        try:
            from opentelemetry.instrumentation.cohere import CohereInstrumentor

            CohereInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "anthropic":
        try:
            from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

            AnthropicInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "bedrock":
        try:
            from opentelemetry.instrumentation.bedrock import BedrockInstrumentor

            BedrockInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "ollama":
        try:
            from opentelemetry.instrumentation.ollama import OllamaInstrumentor

            OllamaInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "gemini":
        try:
            from opentelemetry.instrumentation.google_generativeai import (
                GoogleGenerativeAiInstrumentor,
            )

            GoogleGenerativeAiInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "replicate":
        try:
            from opentelemetry.instrumentation.replicate import ReplicateInstrumentor

            ReplicateInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "together_ai":
        try:
            from opentelemetry.instrumentation.together import TogetherAiInstrumentor

            TogetherAiInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "replicate":
        try:
            from opentelemetry.instrumentation.replicate import ReplicateInstrumentor

            ReplicateInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "huggingface":
        try:
            from opentelemetry.instrumentation.transformers import TransformersInstrumentor

            TransformersInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "vertex_ai":
        try:
            from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor

            VertexAIInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    elif provider == "watsonx":
        try:
            from opentelemetry.instrumentation.watsonx import WatsonxInstrumentor

            WatsonxInstrumentor().instrument()
        except ImportError:
            msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    else:
        msg = f"Couldn't instrument {provider}. Try installing `opentelemetry-instrumenation-{provider}"

    if msg:
        print(msg)
        return msg


@action(reads=["history"], writes=["history"])
def generate_answer(
    state: State, model: str, messages: list[dict], __tracer: TracerFactory, msg_to_log=None
):
    if msg_to_log:
        __tracer.log_attribute("message", msg_to_log)

    response = litellm.completion(model=model, messages=messages)
    llm_answer = response.choices[0].message.content

    history = state["history"]
    if history.get(model) is None:
        history[model] = []

    history[model] += [llm_answer]
    return state.update(history=history)


def build_burr_app(source_project: str) -> Application:
    tracker = LocalTrackingClient(project="burr-playground")
    return (
        ApplicationBuilder()
        .with_actions(generate_answer)
        .with_transitions(("generate_answer", "generate_answer"))
        .with_identifiers(app_id=source_project)
        .initialize_from(
            initializer=tracker,
            resume_at_next_action=False,
            default_state={"history": {}},
            default_entrypoint="generate_answer",
        )
        .with_tracker("local", project="burr-playground", use_otel_tracing=True)
        .build()
    )


@st.cache_resource
def get_burr_backend():
    return LocalBackend()


def normalize_spans(spans: list) -> dict:
    nested_dict = {}
    for span in spans:
        key = span.key
        value = span.value

        keys = key.split(".")
        d = nested_dict
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
    return nested_dict


def history_component(normalized_spans):
    # historical data
    with st.expander("History", expanded=True):
        prompts = normalized_spans["gen_ai"]["prompt"].values()
        answer = normalized_spans["gen_ai"]["completion"].values()

        for message in list(prompts) + list(answer):
            role = message.get("role", "assistant")
            with st.chat_message(role):
                st.markdown(message["content"])


def launcher_component(idx, default_provider=0):
    """Menu to select LLM provider and selected model"""
    selected_provider = st.selectbox(
        "Provider",
        options=litellm.models_by_provider.keys(),
        index=default_provider,
        key=f"provider_{idx}",
    )
    selected_model = st.selectbox(
        "Model",
        options=litellm.models_by_provider[selected_provider],
        index=None,
        key=f"model_{idx}",
    )
    st.session_state[f"selected_provider_{idx}"] = selected_provider
    st.session_state[f"selected_model_{idx}"] = selected_model


def get_llm_spans(step):
    chat_span_ids = set()
    for span in step.spans:
        if ".chat" in span.begin_entry.span_name:
            chat_span_ids.add(span.begin_entry.span_id)

    return [attr for attr in step.attributes if attr.span_id in chat_span_ids]


def frontend():
    st.title("🌯 Burr prompt playground")
    backend = get_burr_backend()

    # default value; is overriden at the end of `with st.sidebar:`
    normalized_spans = None
    with st.sidebar:
        st.header("Burr playground")

        # project selection
        selected_project = project_selectbox(backend=backend)
        selected_app = application_selectbox(project=selected_project, backend=backend)
        steps = get_steps(project=selected_project, application=selected_app, backend=backend)

        steps_with_llms = [
            step
            for step in steps
            if any(span for span in step.spans if len(get_llm_spans(step)) > 0)
        ]
        if len(steps_with_llms) == 0:
            st.warning("Select a `Project > Application > Step` that includes LLM requests")
            return

        selected_step = step_selectbox(steps=steps_with_llms)
        relevant_spans = get_llm_spans(selected_step)
        normalized_spans = normalize_spans(relevant_spans)

    # main window
    st.header(
        selected_project.name
        + " : "
        + selected_app.app_id[:10]
        + " : "
        + str(selected_step.step_start_log.sequence_id)
        + "-"
        + selected_step.step_start_log.action
    )

    history_component(normalized_spans)

    messages = list(normalized_spans["gen_ai"]["prompt"].values())

    left, right = st.columns([0.85, 0.15])
    with left:
        new_prompt = st.text_area("Prompt", value=messages[-1]["content"], height=300)

    launcher_0, launcher_1, launcher_2 = st.columns(3)
    with launcher_0:
        launcher_component(0, default_provider=0)
        placeholder_0 = st.empty()

    with launcher_1:
        launcher_component(1, default_provider=3)
        placeholder_1 = st.empty()

    with launcher_2:
        launcher_component(2, default_provider=1)
        placeholder_2 = st.empty()

    with right:
        if st.button("Launch"):
            for i in range(2):
                model = st.session_state.get(f"selected_model_{i}")
                if model is None:
                    continue

                instrumentation_msg = instrument(st.session_state[f"selected_provider_{i}"])
                burr_app = build_burr_app(source_project=selected_project.name)
                _, _, state = burr_app.step(
                    inputs={
                        "model": model,
                        "messages": messages[:-1] + [{"role": "user", "content": new_prompt}],
                        "msg_to_log": instrumentation_msg,
                    }
                )

                locals()[f"placeholder_{i}"].container().write(state["history"][model][-1])


if __name__ == "__main__":
    frontend()
