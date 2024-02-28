import uuid

import application as chatbot_application
import streamlit as st

import burr.core


def render_chat_message(chat_item: dict):
    content = chat_item["content"]
    content_type = chat_item["type"]
    role = chat_item["role"]
    with st.chat_message(role):
        if content_type == "image":
            st.image(content)
        elif content_type == "code":
            st.code(content)
        elif content_type == "text":
            st.write(content)


def initialize_app() -> burr.core.Application:
    if "burr_app" not in st.session_state:
        st.session_state.burr_app = chatbot_application.application(
            use_hamilton=False, app_id=f"chat:{str(uuid.uuid4())[0:6]}"
        )
    return st.session_state.burr_app


def main():
    st.title("Chatbot example with Burr")
    app = initialize_app()

    prompt = st.chat_input("Ask me a question!", key="chat_input")
    for chat_message in app.state.get("chat_history", []):
        render_chat_message(chat_message)
    if prompt:
        for action, result, state in app.iterate(
            inputs={"prompt": prompt}, halt_after=["response"]
        ):
            if action.name in ["prompt", "response"]:
                render_chat_message(result["chat_item"])


if __name__ == "__main__":
    main()
