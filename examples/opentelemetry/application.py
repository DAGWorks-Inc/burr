import os
from typing import Optional, Tuple

import openai
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from traceloop.sdk import Traceloop

from burr.core import Application, ApplicationBuilder, State, default, when
from burr.core.action import action
from burr.core.graph import GraphBuilder
from burr.integrations.opentelemetry import OpenTelemetryBridge
from burr.visibility import TracerFactory

MODES = {
    "answer_question": "text",
    "generate_image": "image",
    "generate_code": "code",
    "unknown": "text",
}


@action(reads=[], writes=["chat_history", "prompt"])
def process_prompt(state: State, prompt: str, __tracer: TracerFactory) -> Tuple[dict, State]:
    result = {"chat_item": {"role": "user", "content": prompt, "type": "text"}}
    __tracer.log_attributes(prompt=prompt)
    return result, state.wipe(keep=["prompt", "chat_history"]).append(
        chat_history=result["chat_item"]
    ).update(prompt=prompt)


@action(reads=["prompt"], writes=["safe"])
def check_safety(state: State, __tracer: TracerFactory) -> Tuple[dict, State]:
    with __tracer("check_safety"):
        result = {"safe": "unsafe" not in state["prompt"]}  # quick hack to demonstrate
    return result, state.update(safe=result["safe"])


def _get_openai_client():
    return openai.Client()


@action(reads=["prompt"], writes=["mode"])
def choose_mode(state: State, __tracer: TracerFactory) -> Tuple[dict, State]:
    prompt = (
        f"You are a chatbot. You've been prompted this: {state['prompt']}. "
        f"You have the capability of responding in the following modes: {', '.join(MODES)}. "
        "Please respond with *only* a single word representing the mode that most accurately "
        "corresponds to the prompt. Fr instance, if the prompt is 'draw a picture of a cat', "
        "the mode would be 'generate_image'. If the prompt is 'what is the capital of France', the mode would be 'answer_question'."
        "If none of these modes apply, please respond with 'unknown'."
    )
    with __tracer("query_openai", span_dependencies=["generate_prompt"]):
        client = _get_openai_client()
        result = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
        )
    content = result.choices[0].message.content
    mode = content.lower()
    if mode not in MODES:
        mode = "unknown"
    result = {"mode": mode}
    return result, state.update(**result)


@action(reads=["prompt", "chat_history"], writes=["response"])
def prompt_for_more(state: State) -> Tuple[dict, State]:
    result = {
        "response": {
            "content": "None of the response modes I support apply to your question. Please clarify?",
            "type": "text",
            "role": "assistant",
        }
    }
    return result, state.update(**result)


@action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def chat_response(
    state: State,
    prepend_prompt: str,
    __tracer: TracerFactory,
    model: str = "gpt-3.5-turbo",
) -> Tuple[dict, State]:
    __tracer.log_attributes(model=model, prepend_prompt=prepend_prompt)
    chat_history = state["chat_history"].copy()
    chat_history[-1]["content"] = f"{prepend_prompt}: {chat_history[-1]['content']}"
    chat_history_api_format = [
        {
            "role": chat["role"],
            "content": chat["content"],
        }
        for chat in chat_history
    ]
    client = _get_openai_client()
    with __tracer("query_openai", span_dependencies=["create_openai_client"]):
        result = client.chat.completions.create(
            model=model,
            messages=chat_history_api_format,
        )
    response = result.choices[0].message.content
    result = {"response": {"content": response, "type": MODES[state["mode"]], "role": "assistant"}}
    return result, state.update(**result)


@action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def image_response(
    state: State, __tracer: TracerFactory, model: str = "dall-e-2"
) -> Tuple[dict, State]:
    __tracer.log_attributes(model=model)
    client = _get_openai_client()
    with __tracer("query_openai_image", span_dependencies=["create_openai_client"]):
        result = client.images.generate(
            model=model, prompt=state["prompt"], size="1024x1024", quality="standard", n=1
        )
        response = result.data[0].url
    result = {"response": {"content": response, "type": MODES[state["mode"]], "role": "assistant"}}
    __tracer.log_attributes(response=response)
    return result, state.update(**result)


@action(reads=["response", "safe", "mode"], writes=["chat_history"])
def response(state: State) -> Tuple[dict, State]:
    if not state["safe"]:
        result = {
            "chat_item": {
                "role": "assistant",
                "content": "I'm sorry, I can't respond to that.",
                "type": "text",
            }
        }
    else:
        result = {"chat_item": state["response"]}
    return result, state.append(chat_history=result["chat_item"])


graph = (
    GraphBuilder()
    .with_actions(
        prompt=process_prompt,
        check_safety=check_safety,
        decide_mode=choose_mode,
        generate_image=image_response,
        generate_code=chat_response.bind(
            prepend_prompt="Please respond with *only* code and no other text (at all) to the following:",
        ),
        answer_question=chat_response.bind(
            prepend_prompt="Please answer the following question:",
        ),
        prompt_for_more=prompt_for_more,
        response=response,
    )
    .with_transitions(
        ("prompt", "check_safety", default),
        ("check_safety", "decide_mode", when(safe=True)),
        ("check_safety", "response", default),
        ("decide_mode", "generate_image", when(mode="generate_image")),
        ("decide_mode", "generate_code", when(mode="generate_code")),
        ("decide_mode", "answer_question", when(mode="answer_question")),
        ("decide_mode", "prompt_for_more", default),
        (
            ["generate_image", "answer_question", "generate_code", "prompt_for_more"],
            "response",
        ),
        ("response", "prompt", default),
    )
    .build()
)


def application_burr_as_otel_provider(
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
) -> Application:
    """Runs the application with Burr as the opentelemetry provider"""
    return (
        ApplicationBuilder()
        .with_entrypoint("prompt")
        .with_state(chat_history=[])
        .with_graph(graph)
        .with_tracker(
            project="demo_opentelemetry", params={"storage_dir": storage_dir}, use_otel_tracing=True
        )
        .with_identifiers(app_id=app_id)
        .build()
    )


def application_traceloop_as_otel_provider(
    app_id: Optional[str] = None,
    storage_dir: Optional[str] = "~/.burr",
) -> Application:
    if "TRACELOOP_API_KEY" not in os.environ:
        raise ValueError("Please set the TRACELOOP_API_KEY environment variable")
    Traceloop.init(app_name="burr_demo_traceloop", api_key=os.environ.get("TRACELOOP_API_KEY"))
    return (
        ApplicationBuilder()
        .with_entrypoint("prompt")
        .with_state(chat_history=[])
        .with_graph(graph)
        .with_tracker(project="demo_traceloop", params={"storage_dir": storage_dir})
        .with_hooks(OpenTelemetryBridge())
        .with_identifiers(app_id=app_id)
        .build()
    )


if __name__ == "__main__":
    # Instrument OpenAI API
    OpenAIInstrumentor().instrument()
    # Choose which one to use
    # To use traceloop, uncomment this
    # app = application_traceloop_as_otel_provider()
    # To use Burr, keep this uncommented
    app = application_burr_as_otel_provider()
    app.visualize(output_file_path="statemachine", include_conditions=True, view=True, format="png")
    app.run(halt_after=["response"], inputs={"prompt": "What is the capital of France?"})
