import datetime

import burr.core
from burr.core import Application, State
from burr.core.action import action


@action(reads=[], writes=[])
def dummy_bot(state: State, user_input: str):
    if "time" in user_input:
        current_time = datetime.datetime.now()
        reply = f"It is currently {current_time}"
    else:
        reply = "🤖 Ask me about the time"

    results = dict(content=reply)
    return results, state.update(**results)


def build_application() -> Application:
    return (
        burr.core.ApplicationBuilder()
        .with_actions(dummy_bot)
        .with_transitions(("dummy_bot", "dummy_bot"))
        .with_identifiers(app_id="burr-openai")
        .with_entrypoint("dummy_bot")
        .build()
    )


if __name__ == "__main__":
    app = build_application()
    app.visualize(
        output_file_path="statemachine",
        include_conditions=False,
        view=True,
        format="png",
    )
