import application as counter
import streamlit as st

from burr.integrations.streamlit import (
    AppState,
    Record,
    get_state,
    render_explorer,
    set_slider_to_current,
    update_state,
)


def counter_view(app_state: AppState):
    application = app_state.app
    button = st.button("Forward", use_container_width=True)
    if button:
        step_output = application.step()
        if step_output is not None:
            action, result, state = step_output
            app_state.history.append(Record(state.get_all(), action.name, result))
            set_slider_to_current()
        else:
            application.update_state(application.state.update(counter=0))
            application.reset_to_entrypoint()
            action, result, state = application.step()
            app_state.history.append(Record(state.get_all(), action.name, result))


def retrieve_state():
    if "burr_state" not in st.session_state:
        state = AppState.from_empty(app=counter.application())
    else:
        state = get_state()
    return state


def main():
    st.set_page_config(layout="wide")
    sidebar = st.sidebar
    with sidebar:
        st.markdown(
            """
            <style>
                section[data-testid="stSidebar"] {
                    width: 400px !important; # Set the width to your desired value
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.title("Counting numbers with Burr")
        st.write(
            "This is a simple counter app. It counts to 10, then loops back to 0. You can reset it at any time. "
            "While we know that this is easy to do with a simple loop + streamlit, it highlights the state that Burr manages."
            "Use the slider to rewind/see what happened in the past, and the visualizations to understand how we navigate "
            "through the state machine!"
        )
    app_state = retrieve_state()  # retrieve first so we can use for the ret of the step
    columns = st.columns(2)
    with columns[0]:
        counter_view(app_state)
        with st.container(height=800):
            md_lines = []
            for item in app_state.history:
                if item.action == "counter":
                    md_lines.append(f"Counted to {item.state['counter']}!")
                else:
                    md_lines.append("Looping back! ")
            st.code("\n".join(md_lines), language=None)
    with columns[1]:
        render_explorer(app_state)
    update_state(app_state)  # update so the next iteration knows what to do


if __name__ == "__main__":
    main()
