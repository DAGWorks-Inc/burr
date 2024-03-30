import application as cowsay_application
import streamlit as st

from burr.integrations.streamlit import (
    AppState,
    Record,
    get_state,
    render_explorer,
    set_slider_to_current,
    update_state,
)


def cow_say_view(app_state: AppState):
    application = app_state.app
    button = st.button("Cow say?", use_container_width=True)
    if button:
        step_output = application.step()
        action, result, state = step_output
        app_state.history.append(Record(state.get_all(), action.name, result))
        set_slider_to_current()


def render_cow_said(record: Record):
    cow_said = record.state.get("cow_said")
    cow_should_speak = record.state.get("cow_should_speak")
    with st.chat_message("cow", avatar="🐮" if cow_should_speak and cow_said else "💭"):
        grey = "#A9A9A9"
        if record.action == "cow_should_say":
            if cow_should_speak:
                st.markdown(
                    f"<p style='color: {grey};'>Cow will not speak.</p>", unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<p style='color: {grey};'>Cow will not speak.</p>", unsafe_allow_html=True
                )
        else:
            if cow_said is None:
                st.markdown(f"<p style='color: {grey};'>...</p>", unsafe_allow_html=True)
            if cow_said is not None:
                st.code(cow_said, language="plaintext")


def retrieve_state():
    if "burr_state" not in st.session_state:
        state = AppState.from_empty(app=cowsay_application.application())
    else:
        state = get_state()
    return state


def main():
    st.set_page_config(layout="wide")
    st.title("Talking cows with Burr")
    app_state = retrieve_state()  # retrieve first so we can use for the ret of the step
    columns = st.columns(2)
    with columns[0]:
        cow_say_view(app_state)
        with st.container(height=800):
            for item in app_state.history:
                render_cow_said(item)
    with columns[1]:
        render_explorer(app_state)
    update_state(app_state)  # update so the next iteration knows what to do


if __name__ == "__main__":
    main()
