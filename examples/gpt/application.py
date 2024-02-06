import abc
import functools
from typing import List

import dag
import openai

from burr.core import Action, Application, ApplicationBuilder, State, default, expr, when
from burr.integrations.hamilton import Hamilton, append_state, from_state, update_state
from burr.lifecycle import LifecycleAdapter
from hamilton import driver


class PromptInput(Action):
    @property
    def reads(self) -> list[str]:
        return ["prompt"]

    def run(self, state: State) -> dict:
        return {"processed_prompt": {"role": "user", "content": state["prompt"], "type": "text"}}

    @property
    def writes(self) -> list[str]:
        return ["chat_history"]

    def update(self, result: dict, state: State) -> State:
        return state.wipe(keep=["prompt", "chat_history"]).append(
            chat_history=result["processed_prompt"]
        )


class SafetyCheck(Action):
    @property
    def reads(self) -> list[str]:
        return ["prompt"]

    def run(self, state: State) -> dict:
        if "unsafe" in state["prompt"]:
            # quick for testing
            return {"safe": False}
        return {"safe": True}

    @property
    def writes(self) -> list[str]:
        return ["safe"]

    def update(self, result: dict, state: State) -> State:
        return state.update(safe=result["safe"])


MODES = [
    "answer_question",
    "draw_image",
    "generate_code",
]


@functools.lru_cache(maxsize=None)
def _get_openai_client():
    return openai.Client()


class ChooseMode(Action):
    def __init__(
        self, client: openai.Client = _get_openai_client(), model: str = "gpt-4", modes=tuple(MODES)
    ):
        super(ChooseMode, self).__init__()
        self.client = client
        self.model = model
        self.modes = modes

    @property
    def reads(self) -> list[str]:
        return ["prompt"]

    def run(self, state: State) -> dict:
        prompt = (
            f"You are a chatbot. You've been prompted this: {state['prompt']}. "
            f"You have the capability of responding in the following modes: {', '.join(self.modes)}. "
            "Please respond with *only* a single word representing the mode that most accurately"
            " corresponds to the prompt. Fr instance, if the prompt is 'draw a picture of a cat', "
            "the mode would be 'image'. If the prompt is 'what is the capital of France', the mode would be 'text'."
            "If none of these modes apply, please respond with 'unknown'."
        )
        result = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
        )
        content = result.choices[0].message.content
        mode = content.lower()
        if mode not in self.modes:
            mode = "unknown"
        return {"mode": mode}

    @property
    def writes(self) -> list[str]:
        return ["mode"]

    def update(self, result: dict, state: State) -> State:
        return state.update(mode=result["mode"])


class BaseChatCompletion(Action, abc.ABC):
    @property
    def reads(self) -> list[str]:
        return ["prompt", "chat_history"]

    @abc.abstractmethod
    def chat_response(self, state: State) -> dict:
        pass

    def run(self, state: State) -> dict:
        return {"response": self.chat_response(state)}

    @property
    def writes(self) -> list[str]:
        return ["response"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


class DontKnowResponse(BaseChatCompletion):
    def __init__(self, modes=tuple(MODES)):
        super(DontKnowResponse, self).__init__()
        self.modes = modes

    def chat_response(self, state: State) -> dict:
        return {
            "content": f"None of the response modes I support: ({','.join(self.modes)}) "
            f"apply to your question. Please clarify?",
            "type": "text",
            "role": "assistant",
        }


def _get_text_response(chat_history: list[dict], model: str, client: openai.Client) -> str:
    chat_history_api_format = [
        {
            "role": chat["role"],
            "content": chat["content"],
        }
        for chat in chat_history
    ]
    result = client.chat.completions.create(
        model=model,
        messages=chat_history_api_format,
    )
    return result.choices[0].message.content


class AnswerQuestionResponse(BaseChatCompletion):
    def __init__(self, client: openai.Client = _get_openai_client(), model: str = "gpt-4"):
        super(AnswerQuestionResponse, self).__init__()
        self.client = client
        self.model = model

    def chat_response(self, state: State) -> dict:
        chat_history = state["chat_history"].copy()
        chat_history[-1][
            "content"
        ] = f"Please answer the following question: {chat_history[-1]['content']}"
        response = _get_text_response(chat_history, self.model, self.client)
        return {"content": response, "type": "text", "role": "assistant"}


class GenerateImageResponse(BaseChatCompletion):
    def __init__(self, client: openai.Client = _get_openai_client(), model: str = "dall-e-2"):
        super(GenerateImageResponse, self).__init__()
        self.client = client
        self.model = model

    def chat_response(self, state: State) -> dict:
        result = self.client.images.generate(
            model=self.model, prompt=state["prompt"], size="1024x1024", quality="standard", n=1
        )
        return {"content": result.data[0].url, "type": "image", "role": "assistant"}


class GenerateCodeResponse(BaseChatCompletion):
    def __init__(self, client: openai.Client = _get_openai_client(), model: str = "gpt-4"):
        super(GenerateCodeResponse, self).__init__()
        self.client = client
        self.model = model

    def chat_response(self, state: State) -> dict:
        chat_history = state["chat_history"].copy()
        chat_history[-1]["content"] = (
            f"Please answer the following question, "
            f"responding *only* with code, and nothing else: {chat_history[-1]['content']}"
        )
        return {
            "content": _get_text_response(state["chat_history"], self.model, self.client),
            "type": "code",
            "role": "assistant",
        }


class Response(Action):
    @property
    def reads(self) -> list[str]:
        return ["response", "safe", "mode"]

    def run(self, state: State) -> dict:
        if not state["safe"]:
            return {
                "processed_response": {
                    "role": "assistant",
                    "content": "I'm sorry, I can't respond to that.",
                    "type": "text",
                }
            }
        return {"processed_response": state["response"]}

    @property
    def writes(self) -> list[str]:
        return ["chat_history"]

    def update(self, result: dict, state: State) -> State:
        return state.append(chat_history=result["processed_response"])


class Error(Action):
    @property
    def reads(self) -> list[str]:
        return ["error"]

    def run(self, state: State) -> dict:
        return {
            "chat_record": {"role": "assistant", "content": str(state["error"]), "type": "error"}
        }

    @property
    def writes(self) -> list[str]:
        return ["chat_history"]

    def update(self, result: dict, state: State) -> State:
        return state.append(chat_history=result["chat_record"])


def base_application(hooks: List[LifecycleAdapter] = []):
    return (
        ApplicationBuilder()
        .with_actions(
            prompt=PromptInput(),
            check_safety=SafetyCheck(),
            decide_mode=ChooseMode(),
            generate_image=GenerateImageResponse(),
            generate_code=GenerateCodeResponse(),
            answer_question=AnswerQuestionResponse(),
            prompt_for_more=DontKnowResponse(),
            response=Response(),
            error=Error(),
        )
        .with_entrypoint("prompt")
        .with_state(chat_history=[])
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
                when(error=None),
            ),
            (
                ["generate_image", "answer_question", "generate_code", "prompt_for_more"],
                "error",
                expr("error is not None"),
            ),
            ("response", "prompt", default),
            ("error", "prompt", default),
        )
        .with_hooks(*hooks)
        .build()
    )


def hamilton_application(hooks: List[LifecycleAdapter] = []):
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
            error=Error(),
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
                when(error=None),
            ),
            (
                ["generate_image", "answer_question", "generate_code", "prompt_for_more"],
                "error",
                expr("error is not None"),
            ),
            ("response", "prompt", default),
            ("error", "prompt", default),
        )
        .with_hooks(*hooks)
        .build()
    )
    return application


def application(use_hamilton: bool, hooks: List[LifecycleAdapter] = []) -> Application:
    if use_hamilton:
        return hamilton_application(hooks)
    return base_application(hooks)


if __name__ == "__main__":
    app = application(use_hamilton=True)
    # state, result = app.run(until=["result"])
    app.visualize(output_file_path="gpt", include_conditions=False, view=True, format="png")
    # assert state["counter"] == 10
    # print(state["counter"])
