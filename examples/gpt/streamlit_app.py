from typing import Optional

import application as chatbot_application
import streamlit as st

from burr.integrations.streamlit import (
    AppState,
    Record,
    get_state,
    render_explorer,
    set_slider_to_current,
    update_state,
)


def render_chat_message(record: Record):
    if record.action in ["prompt", "response"]:
        recent_chat_message = record.state["chat_history"][-1]
        content = recent_chat_message["content"]
        content_type = recent_chat_message["type"]
        role = recent_chat_message["role"]
        with st.chat_message(role):
            if content_type == "image":
                st.image(content)
            elif content_type == "code":
                st.code(content)
            elif content_type == "text":
                st.write(content)
            elif content_type == "error":
                st.error(content)


def retrieve_state():
    if "burr_state" not in st.session_state:
        state = AppState.from_empty(
            app=chatbot_application.application(use_hamilton=False),
        )
    else:
        state = get_state()
    return state


def chatbot_step(app_state: AppState, prompt: Optional[str]) -> bool:
    """Pushes state forward for the chatbot. Returns whether or not to rerun the app.

    :param app_state: State of the app
    :param prompt: Prompt to set the chatbot to. If this is None it means it should continue and not be reset.
    :return:
    """
    if prompt is not None:
        # We need to update
        app_state.app.update_state(app_state.app.state.update(prompt=prompt))
        st.session_state.running = True  # set to running
    # if its not running this is a no-op
    if not st.session_state.get("running", False):
        return False
    application = app_state.app
    step_output = application.step()
    if step_output is None:
        st.session_state.running = False
        return False
    action, result, state = step_output
    app_state.history.append(Record(state.get_all(), action.name, result))
    set_slider_to_current()
    if action.name == "response":
        # we've gotten to the end
        st.session_state.running = False
        return True  # run one last time
    return True


def main():
    st.set_page_config(layout="wide")
    st.title("Chatbot example with Burr")
    app_state = retrieve_state()  # retrieve first so we can use for the ret of the step
    columns = st.columns(2)
    with columns[0]:
        prompt = st.chat_input(
            "...", disabled=st.session_state.get("running", False), key="chat_input"
        )
        should_rerun = chatbot_step(app_state, prompt)
        with st.container(height=850):
            for item in app_state.history:
                render_chat_message(item)
    with columns[1]:
        render_explorer(app_state)
    update_state(app_state)  # update so the next iteration knows what to do
    if should_rerun:
        st.rerun()


if __name__ == "__main__":
    main()
