from typing import Tuple

from burr.core import Action, Application, ApplicationBuilder, State, default, expr
from burr.core.action import action
from burr.integrations import hamilton
from burr.lifecycle import PostRunStepHook

from hamilton import dataflows, driver

caption_images = dataflows.import_module("caption_images", "elijahbenizzy")
generate_images = dataflows.import_module("generate_images", "elijahbenizzy")


caption_image_driver = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(caption_images)
    .build()
)

generate_image_driver = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(generate_images)
    .build()
)

# procedural way to do this
@action(reads=["image_location"], writes=["image_caption"])
def image_caption(state: State) -> Tuple[dict, State]:
    result = caption_image_driver.execute([
        "generated_caption"
    ], inputs={"image_url": state["image_location"]})
    updates = {
        "image_caption": result["generated_caption"],
    }
    return result, state.update(**updates)

# procedural way to do this
@action(reads=["image_caption", "iteration"],
        writes=["image_location", "iteration"])
def image_generation(state: State) -> Tuple[dict, State]:
    result = generate_image_driver.execute([
        "generated_image"
    ], inputs={"image_generation_prompt": state["image_caption"]})
    updates = {
        "iteration": state["iteration"] + 1,
        "image_location": result["generated_image"],
    }
    return result, state.update(**updates)

@action(reads=[], writes=[])
def terminal_step(state: State) -> Tuple[dict, State]:
    print("This is a terminal step hook.")
    return {}, state



def main():
    _caption = hamilton.Hamilton(
        inputs={"image_url": hamilton.from_state("image_location")},
        outputs={"generated_caption": hamilton.update_state("image_caption")},
        driver=caption_image_driver,
    )
    _image = hamilton.Hamilton(
        inputs={"image_generation_prompt": hamilton.from_state("image_caption")},
        outputs={"generated_image": hamilton.update_state("image_location")},
        driver=generate_image_driver,
    )
    app = (
        ApplicationBuilder()
        .with_state(
            iteration=0,
            image_location="telephone_graph.png",
            image_caption=""
        )
        # .with_actions(
        #     caption=image_caption,
        #     image=image_generation,
        #     terminal=terminal_step,
        # )
        .with_actions(
            caption=_caption,
            image=_image,
            terminal=terminal_step,
        )
        .with_transitions(
            ("caption", "image", default),
            ("image", "terminal", expr("iteration == 2")),
            ("image", "caption", default),
        )
        .with_entrypoint("caption")
        .build()
    )
    return app


if __name__ == "__main__":
    app = main()
    app.visualize(output_file_path="telephone_graph",
                  include_conditions=True, view=True, format="png")
    while True:
        action, result, state  = app.step()
        print("action=====\n", action)
        print("result=====\n", result)
        print("state======\n", state)
        if action.name == "terminal":
            break
