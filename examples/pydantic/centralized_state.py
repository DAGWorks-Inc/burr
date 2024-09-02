import copy
import os
from typing import List, Optional

import openai
import pydantic

from burr.core import ApplicationBuilder, State, action, default, graph, when
from burr.integrations.pydantic import PydanticTypingSystem, pydantic_action
from burr.lifecycle import LifecycleAdapter

MODES = {
    "answer_question": "text",
    "generate_image": "image",
    "generate_code": "code",
    "unknown": "text",
}


class ApplicationState(pydantic.BaseModel):
    chat_history: List[dict[str, str]] = pydantic.Field(default_factory=list)
    prompt: Optional[str]
    has_openai_key: Optional[bool]
    safe: Optional[bool]
    mode: Optional[str]
    response: dict[str, str]


@pydantic_action(reads=[], writes=["chat_history", "prompt"])
def process_prompt(state: ApplicationState, prompt: str) -> ApplicationState:
    state.chat_history.append({"role": "user", "content": prompt, "type": "text"})
    state.prompt = prompt
    return state


@pydantic_action(reads=["prompt"], writes=["safe"])
def check_safety(state: ApplicationState) -> ApplicationState:
    state.safe = "unsafe" not in state.prompt
    return state


def _get_openai_client():
    return openai.Client()


@pydantic_action(reads=["prompt"], writes=["mode"])
def choose_mode(state: ApplicationState) -> ApplicationState:
    prompt = (
        f"You are a chatbot. You've been prompted this: {state.prompt}. "
        f"You have the capability of responding in the following modes: {', '.join(MODES)}. "
        "Please respond with *only* a single word representing the mode that most accurately "
        "corresponds to the prompt. Fr instance, if the prompt is 'draw a picture of a cat', "
        "the mode would be 'generate_image'. If the prompt is 'what is the capital of France', the mode would be 'answer_question'."
        "If none of these modes apply, please respond with 'unknown'."
    )

    result = _get_openai_client().chat.completions.create(
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
    state.mode = mode
    return state


@pydantic_action(reads=["prompt", "chat_history"], writes=["response"])
def prompt_for_more(state: ApplicationState) -> ApplicationState:
    state.response = {
        "content": "None of the response modes I support apply to your question. Please clarify?",
        "type": "text",
        "role": "assistant",
    }
    return state


@action(reads=[], writes=["has_openai_key"])
def check_openai_key(state: State) -> State:
    result = {"has_openai_key": "OPENAI_API_KEY" in os.environ}
    return state.update(**result)


@pydantic_action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def chat_response(
    state: ApplicationState,
    prepend_prompt: str,
    model: str = "gpt-3.5-turbo",
) -> ApplicationState:
    chat_history = copy.deepcopy(state.chat_history)
    chat_history[-1]["content"] = f"{prepend_prompt}: {chat_history[-1]['content']}"
    chat_history_api_format = [
        {
            "role": chat["role"],
            "content": chat["content"],
        }
        for chat in chat_history
    ]
    client = _get_openai_client()
    result = client.chat.completions.create(
        model=model,
        messages=chat_history_api_format,
    )
    response = result.choices[0].message.content
    state.response = {"content": response, "type": MODES[state.mode], "role": "assistant"}
    return state


@pydantic_action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def image_response(state: ApplicationState, model: str = "dall-e-2") -> ApplicationState:
    client = _get_openai_client()
    result = client.images.generate(
        model=model, prompt=state.prompt, size="1024x1024", quality="standard", n=1
    )
    response = result.data[0].url
    state.response = {"content": response, "type": MODES[state.mode], "role": "assistant"}
    return state


@pydantic_action(reads=["response", "mode", "safe", "has_openai_key"], writes=["chat_history"])
def response(state: ApplicationState) -> ApplicationState:
    if not state.has_openai_key:
        chat_item = {
            "role": "assistant",
            "content": "You have not set an API key for [OpenAI](https://www.openai.com). Do this "
            "by setting the environment variable `OPENAI_API_KEY` to your key. "
            "You can get a key at [OpenAI](https://platform.openai.com). "
            "You can still look at chat history/examples.",
            "type": "error",
        }
    elif not state.safe:
        chat_item = {
            "role": "assistant",
            "content": "I'm sorry, I can't respond to that.",
            "type": "error",
        }
    else:
        chat_item = state.response
    state.chat_history.append(chat_item)
    return state


graph_object = (
    graph.GraphBuilder()
    .with_actions(
        prompt=process_prompt,
        check_openai_key=check_openai_key,
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
        ("prompt", "check_openai_key", default),
        ("check_openai_key", "check_safety", when(has_openai_key=True)),
        ("check_openai_key", "response", default),
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


def application(
    hooks: Optional[List[LifecycleAdapter]] = None,
    project_id: str = "test_centralized_state",
):
    if hooks is None:
        hooks = []
    # we're initializing above so we can load from this as well
    # we could also use `with_tracker("local", project=project_id, params={"storage_dir": storage_dir})`
    return (
        ApplicationBuilder()
        .with_graph(graph_object)
        # initializes from the tracking log if it does not already exist
        .with_hooks(*hooks)
        .with_tracker("local", project=project_id)
        .with_entrypoint("prompt")
        .with_state(
            ApplicationState(
                chat_history=[],
            )
        )
        .with_typing(PydanticTypingSystem(model_type=ApplicationState))
        .build()
    )


if __name__ == "__main__":
    app = application()
    # app.visualize(
    #     output_file_path="statemachine", include_conditions=False, view=True, format="png"
    # )
    action, result, state = app.run(
        halt_after=["response"], inputs={"prompt": "Who was Aaron Burr, sir?"}
    )
    state.data
