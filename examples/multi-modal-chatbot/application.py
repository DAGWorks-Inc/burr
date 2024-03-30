import copy
import os
from typing import List, Optional, Tuple

import openai
from hamilton import driver

from burr.core import Application, ApplicationBuilder, State, default, when
from burr.core.action import action
from burr.integrations.hamilton import Hamilton, append_state, from_state, update_state
from burr.lifecycle import LifecycleAdapter
from burr.tracking import LocalTrackingClient

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


@action(reads=[], writes=["has_openai_key"])
def check_openai_key(state: State) -> Tuple[dict, State]:
    result = {"has_openai_key": "OPENAI_API_KEY" in os.environ}
    return result, state.update(**result)


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
    state: State, prepend_prompt: str, display_type: str = "text", model: str = "gpt-3.5-turbo"
) -> Tuple[dict, State]:
    chat_history = copy.deepcopy(state["chat_history"])
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
    result = {"response": {"content": response, "type": MODES[state["mode"]], "role": "assistant"}}
    return result, state.update(**result)


@action(reads=["prompt", "chat_history", "mode"], writes=["response"])
def image_response(state: State, model: str = "dall-e-2") -> Tuple[dict, State]:
    """Generates an image response to the prompt. Optional save function to save the image to a URL."""
    client = _get_openai_client()
    result = client.images.generate(
        model=model, prompt=state["prompt"], size="1024x1024", quality="standard", n=1
    )
    response = result.data[0].url
    result = {"response": {"content": response, "type": MODES[state["mode"]], "role": "assistant"}}
    return result, state.update(**result)


@action(reads=["response", "mode", "safe", "has_openai_key"], writes=["chat_history"])
def response(state: State) -> Tuple[dict, State]:
    if not state["has_openai_key"]:
        result = {
            "chat_item": {
                "role": "assistant",
                "content": "You have not set an API key for [OpenAI](https://www.openai.com). Do this "
                "by setting the environment variable `OPENAI_API_KEY` to your key. "
                "You can get a key at [OpenAI](https://platform.openai.com). "
                "You can still look at chat history/examples.",
                "type": "error",
            }
        }
    elif not state["safe"]:
        result = {
            "chat_item": {
                "role": "assistant",
                "content": "I'm sorry, I can't respond to that.",
                "type": "error",
            }
        }
    else:
        result = {"chat_item": state["response"]}
    return result, state.append(chat_history=result["chat_item"])


def base_application(
    hooks: List[LifecycleAdapter],
    app_id: str,
    storage_dir: str,
    project_id: str,
):
    if hooks is None:
        hooks = []
    # we're initializing above so we can load from this as well
    # we could also use `with_tracker("local", project=project_id, params={"storage_dir": storage_dir})`
    tracker = LocalTrackingClient(project=project_id, storage_dir=storage_dir)
    return (
        ApplicationBuilder()
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
        # initializes from the tracking log if it does not already exist
        .initialize_from(
            tracker,
            resume_at_next_action=False,  # always resume from entrypoint in the case of failure
            default_state={"chat_history": []},
            default_entrypoint="prompt",
        )
        .with_hooks(*hooks)
        .with_tracker(tracker)
        .with_identifiers(app_id=app_id)
        .build()
    )


def hamilton_application(
    hooks: List[LifecycleAdapter], app_id: str, storage_dir: str, project_id: str
):
    import dag

    dr = driver.Driver({"provider": "openai"}, dag)  # TODO -- add modules
    Hamilton.set_driver(dr)
    application = (
        ApplicationBuilder()
        .with_state(chat_history=[], prompt="Draw an image of a turtle saying 'hello, world'")
        .with_entrypoint("prompt")
        .with_state(chat_history=[])
        .with_actions(
            prompt=Hamilton(
                inputs={"prompt": from_state("prompt")},
                outputs={"processed_prompt": append_state("chat_history")},
            ),
            check_safety=Hamilton(
                inputs={"prompt": from_state("prompt")},
                outputs={"safe": update_state("safe")},
            ),
            decide_mode=Hamilton(
                inputs={"prompt": from_state("prompt")},
                outputs={"mode": update_state("mode")},
            ),
            generate_image=Hamilton(
                inputs={"prompt": from_state("prompt")},
                outputs={"generated_image": update_state("response")},
            ),
            generate_code=Hamilton(  # TODO -- implement
                inputs={"chat_history": from_state("chat_history")},
                outputs={"generated_code": update_state("response")},
            ),
            answer_question=Hamilton(  # TODO -- implement
                inputs={"chat_history": from_state("chat_history")},
                outputs={"answered_question": update_state("response")},
            ),
            prompt_for_more=Hamilton(
                inputs={},
                outputs={"prompt_for_more": update_state("response")},
            ),
            response=Hamilton(
                inputs={
                    "response": from_state("response"),
                    "safe": from_state("safe"),
                    "mode": from_state("mode"),
                },
                outputs={"processed_response": append_state("chat_history")},
            ),
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
        .with_hooks(*hooks)
        .with_identifiers(app_id=app_id)
        .with_tracker("local", project=project_id, params={"storage_dir": storage_dir})
        .build()
    )
    return application


def application(
    use_hamilton: bool,
    app_id: Optional[str] = None,
    project_id: str = "demo:chatbot",
    storage_dir: Optional[str] = "~/.burr",
    hooks: Optional[List[LifecycleAdapter]] = None,
) -> Application:
    if use_hamilton:
        return hamilton_application(hooks, app_id, storage_dir, project_id=project_id)
    return base_application(hooks, app_id, storage_dir, project_id=project_id)


if __name__ == "__main__":
    app = application(use_hamilton=False)
    app.visualize(output_file_path="digraph", include_conditions=False, view=True, format="png")
