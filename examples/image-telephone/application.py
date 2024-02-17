from typing import Tuple

from burr.core import Action, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.integrations import hamilton
from burr.lifecycle import PostRunStepHook
from hamilton import dataflows, driver

caption_images = dataflows.import_module("caption_images", "elijahbenizzy")
generate_images = dataflows.import_module("generate_images", "elijahbenizzy")


caption_image_driver = driver.Builder().with_config({}).with_modules(caption_images).build()

generate_image_driver = driver.Builder().with_config({}).with_modules(generate_images).build()


class PrintStepHook(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        print("action=====\n", action)
        print("state======\n", state)


# procedural way to do this
@action(
    reads=["current_image_location"],
    writes=["current_image_caption", "image_location_history"],
)
def image_caption(state: State) -> Tuple[dict, State]:
    current_image = state["current_image_location"]
    result = caption_image_driver.execute(
        ["generated_caption"], inputs={"image_url": current_image}
    )
    updates = {
        "current_image_caption": result["generated_caption"],
    }
    return result, state.update(**updates).append(image_location_history=current_image)


# procedural way to do this
@action(
    reads=["current_image_caption"],
    writes=["current_image_location", "image_caption_history"],
)
def image_generation(state: State) -> Tuple[dict, State]:
    current_caption = state["current_image_caption"]
    result = generate_image_driver.execute(
        ["generated_image"], inputs={"image_generation_prompt": current_caption}
    )
    updates = {
        "current_image_location": result["generated_image"],
    }
    return result, state.update(**updates).append(image_caption_history=current_caption)


@action(reads=[], writes=[])
def terminal_step(state: State) -> Tuple[dict, State]:
    return {}, state


def regular_action_main():
    """This shows how one might define functions to be nodes."""
    app = (
        ApplicationBuilder()
        .with_state(
            current_image_location="telephone_graph.png",
            current_image_caption="",
            image_location_history=[],
            image_caption_history=[],
        )
        .with_actions(
            caption=image_caption,
            image=image_generation,
            terminal=terminal_step,
        )
        .with_transitions(
            ("caption", "image", default),
            ("image", "terminal", expr("len(image_caption_history) == 2")),
            ("image", "caption", default),
        )
        .with_entrypoint("caption")
        .with_hooks(PrintStepHook())
        .build()
    )
    return app


def hamilton_action_main():
    """This shows how to use the Hamilton syntactic wrapper for the nodes."""

    _caption = hamilton.Hamilton(
        inputs={"image_url": hamilton.from_state("current_image_location")},
        outputs={
            "generated_caption": hamilton.update_state("current_image_caption"),
            "image_url": hamilton.append_state("image_location_history"),
        },
        driver=caption_image_driver,
    )
    _image = hamilton.Hamilton(
        inputs={"image_generation_prompt": hamilton.from_state("current_image_caption")},
        outputs={
            "generated_image": hamilton.update_state("current_image_location"),
            "image_generation_prompt": hamilton.append_state("image_caption_history"),
        },
        driver=generate_image_driver,
    )
    app = (
        ApplicationBuilder()
        .with_state(
            current_image_location="telephone_graph.png",
            current_image_caption="",
            image_location_history=[],
            image_caption_history=[],
        )
        .with_actions(
            caption=_caption,
            image=_image,
            terminal=terminal_step,
        )
        .with_transitions(
            ("caption", "image", default),
            ("image", "terminal", expr("len(image_caption_history) == 2")),
            ("image", "caption", default),
        )
        .with_entrypoint("caption")
        .with_hooks(PrintStepHook())
        .build()
    )
    return app


if __name__ == "__main__":
    import random

    coin_flip = random.choice([True, False])
    if coin_flip:
        app = hamilton_action_main()
    else:
        app = regular_action_main()
    app.visualize(
        output_file_path="telephone_graph", include_conditions=True, view=True, format="png"
    )
    if coin_flip:
        app.run(until=["terminal"])
    else:
        # alternate way to run:
        while True:
            action, result, state = app.step()
            print("action=====\n", action)
            print("result=====\n", result)
            print("state======\n", state)
            if action.name == "terminal":
                break
