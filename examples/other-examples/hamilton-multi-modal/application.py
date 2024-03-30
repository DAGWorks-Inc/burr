from typing import List

import dag
from hamilton import driver

from burr.core import ApplicationBuilder, default, when
from burr.integrations.hamilton import Hamilton, append_state, from_state, update_state
from burr.lifecycle import LifecycleAdapter


def application(hooks: List[LifecycleAdapter], app_id: str, storage_dir: str, project_id: str):
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
