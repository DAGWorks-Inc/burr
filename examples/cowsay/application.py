import random
import time
from typing import List, Optional

import cowsay

from burr.core import Action, Application, ApplicationBuilder, State, default, expr
from burr.lifecycle import PostRunStepHook


class CowSay(Action):
    def __init__(self, say_what: List[Optional[str]]):
        super(CowSay, self).__init__()
        self.say_what = say_what

    @property
    def reads(self) -> list[str]:
        return []

    def run(self, state: State) -> dict:
        say_what = random.choice(self.say_what)
        return {
            "cow_said": cowsay.get_output_string("cow", say_what) if say_what is not None else None
        }

    @property
    def writes(self) -> list[str]:
        return ["cow_said"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


class CowShouldSay(Action):
    @property
    def reads(self) -> list[str]:
        return []

    def run(self, state: State) -> dict:
        if not random.randint(0, 3):
            return {"cow_should_speak": True}
        return {"cow_should_speak": False}

    @property
    def writes(self) -> list[str]:
        return ["cow_should_speak"]

    def update(self, result: dict, state: State) -> State:
        return state.update(**result)


class PrintWhatTheCowSaid(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        if action.name != "cow_should_say" and state["cow_said"] is not None:
            print(state["cow_said"])


class CowCantSpeakFast(PostRunStepHook):
    def __init__(self, sleep_time: float):
        super(PostRunStepHook, self).__init__()
        self.sleep_time = sleep_time

    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        if action.name != "cow_should_say":  # no need to print if we're not saying anything
            time.sleep(self.sleep_time)


def application(in_terminal: bool = False) -> Application:
    hooks = (
        [
            PrintWhatTheCowSaid(),
            CowCantSpeakFast(sleep_time=2.0),
        ]
        if in_terminal
        else []
    )
    return (
        ApplicationBuilder()
        .with_state(
            cow_said=None,
        )
        .with_actions(
            say_nothing=CowSay([None]),
            say_hello=CowSay(["Hello world!", "What's up?", "Are you Aaron Burr, sir?"]),
            cow_should_say=CowShouldSay(),
        )
        .with_transitions(
            ("cow_should_say", "say_hello", expr("cow_should_speak")),
            ("say_hello", "cow_should_say", default),
            ("cow_should_say", "say_nothing", expr("not cow_should_speak")),
            ("say_nothing", "cow_should_say", default),
        )
        .with_entrypoint("cow_should_say")
        .with_hooks(*hooks)
        .build()
    )


if __name__ == "__main__":
    app = application(in_terminal=True)
    app.visualize(output_file_path="cowsay.png", include_conditions=True, view=True)
    while True:
        state, result, action = app.step()
