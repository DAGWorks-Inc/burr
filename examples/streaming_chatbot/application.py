from typing import List, Optional, Tuple

import openai

from burr.core import ApplicationBuilder, State, default, when
from burr.core.action import action, streaming_action
from burr.lifecycle import LifecycleAdapter

MODES = {
    "answer_question": "text",
    "generate_image": "image",
    "generate_code": "code",
    "unknown": "text",
}


@action(reads=[], writes=["chat_history", "prompt"])
def process_prompt(state: State, prompt: str) -> Tuple[dict, State]:
    result = {"chat_item": {"role": "user", "content": prompt, "type": "text"}}
    return result, state.wipe(keep=["prompt", "chat_history"]).append(
        chat_history=result["chat_item"]
    ).update(prompt=prompt)


@action(reads=["prompt"], writes=["safe"])
def check_safety(state: State) -> Tuple[dict, State]:
    result = {"safe": "unsafe" not in state["prompt"]}  # quick hack to demonstrate
    return result, state.update(safe=result["safe"])


def _get_openai_client():
    return openai.Client()


@action(reads=["prompt"], writes=["mode"])
def choose_mode(state: State) -> Tuple[dict, State]:
    prompt = (
        f"You are a chatbot. You've been prompted this: {state['prompt']}. "
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
    result = {"mode": mode}
    return result, state.update(**result)


@action(reads=["prompt", "chat_history"], writes=["response"])
def prompt_for_more(state: State) -> Tuple[dict, State]:
    """Not streaming, as we have the result immediately."""
    result = {
        "response": {
            "content": "None of the response modes I support apply to your question. Please clarify?",
            "type": "text",
            "role": "assistant",
        }
    }
    return result, state.update(**result).append(chat_history=result["response"])


@streaming_action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def chat_response(
    state: State, prepend_prompt: str, model: str = "gpt-3.5-turbo"
) -> Tuple[dict, State]:
    """Streaming action, as we don't have the result immediately. This makes it more interactive"""
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
    result = client.chat.completions.create(
        model=model, messages=chat_history_api_format, stream=True
    )
    buffer = []
    for chunk in result:
        chunk_str = chunk.choices[0].delta.content
        if chunk_str is None:
            continue  # consider breaking...
        buffer.append(chunk_str)
        yield {
            "response": {"content": chunk_str, "type": MODES[state["mode"]], "role": "assistant"}
        }

    result = {
        "response": {"content": "".join(buffer), "type": MODES[state["mode"]], "role": "assistant"}
    }
    return result, state.update(**result).append(chat_history=result["response"])


@action(reads=["prompt", "chat_history"], writes=["response"])
def unsafe_response(state: State) -> Tuple[dict, State]:
    result = {
        "response": {
            "content": "I am afraid I can't respond to that...",
            "type": "text",
            "role": "assistant",
        }
    }
    return result, state.update(**result).append(chat_history=result["response"])


@action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def image_response(state: State, model: str = "dall-e-2") -> Tuple[dict, State]:
    client = _get_openai_client()
    result = client.images.generate(
        model=model, prompt=state["prompt"], size="1024x1024", quality="standard", n=1
    )
    response = result.data[0].url
    result = {"response": {"content": response, "type": MODES[state["mode"]], "role": "assistant"}}
    return result, state.update(**result).append(chat_history=result["response"])


def application(hooks: List[LifecycleAdapter], app_id: Optional[str] = None):
    if hooks is None:
        hooks = []
    return (
        ApplicationBuilder()
        .with_actions(
            prompt=process_prompt,
            check_safety=check_safety,
            unsafe_response=unsafe_response,
            decide_mode=choose_mode,
            generate_image=image_response,
            generate_code=chat_response.bind(
                prepend_prompt="Please respond with *only* code and no other text (at all) to the following:",
            ),
            answer_question=chat_response.bind(
                prepend_prompt="Please answer the following question:",
            ),
            prompt_for_more=prompt_for_more,
        )
        .with_entrypoint("prompt")
        .with_state(chat_history=[])
        .with_transitions(
            ("prompt", "check_safety", default),
            ("check_safety", "decide_mode", when(safe=True)),
            ("check_safety", "unsafe_response", default),
            ("decide_mode", "generate_image", when(mode="generate_image")),
            ("decide_mode", "generate_code", when(mode="generate_code")),
            ("decide_mode", "answer_question", when(mode="answer_question")),
            ("decide_mode", "prompt_for_more", default),
            (
                [
                    "generate_image",
                    "answer_question",
                    "generate_code",
                    "prompt_for_more",
                    "unsafe_response",
                ],
                "prompt",
            ),
        )
        .with_hooks(*hooks)
        .with_tracker("demo:chatbot_streaming", params={"app_id": app_id})
        .build()
    )


# TODO -- replace these with action tags when we have the availability
TERMINAL_ACTIONS = [
    "generate_image",
    "answer_question",
    "generate_code",
    "prompt_for_more",
    "unsafe_response",
]
if __name__ == "__main__":
    app = application(hooks=[])
    app.visualize(output_file_path="digraph", include_conditions=False, view=True, format="png")
