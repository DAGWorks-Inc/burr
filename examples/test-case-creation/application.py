"""This file is truncated to just the relevant parts for the example."""
from typing import Tuple

import openai

from burr.core import State
from burr.core.action import action

# Reminder: This file is truncated to just the relevant parts for the example.

MODES = {
    "answer_question": "text",
    "generate_image": "image",
    "generate_code": "code",
    "unknown": "text",
}


def _get_openai_client():
    return openai.Client()


@action(reads=["prompt"], writes=["mode"])
def choose_mode(state: State) -> Tuple[dict, State]:
    prompt = (
        f"You are a chatbot. You've been prompted this: {state['prompt']}. "
        f"You have the capability of responding in the following modes: {', '.join(MODES)}. "
        "Please respond with *only* a single word representing the mode that most accurately "
        "corresponds to the prompt. For instance, if the prompt is 'draw a picture of a cat', "
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


# Reminder: this file is truncated to just the relevant parts for the example.
