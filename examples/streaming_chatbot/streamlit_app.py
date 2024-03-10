import uuid

import application as chatbot_application
import streamlit as st

import burr.core
from burr.core.action import StreamingResultContainer


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


def render_streaming_chat_message(stream: StreamingResultContainer):
    with st.chat_message("assistant"):
        st.write_stream(item["response"]["content"] for item in stream)


def initialize_app() -> burr.core.Application:
    if "burr_app" not in st.session_state:
        st.session_state.burr_app = chatbot_application.application(
            app_id=f"chat_streaming:{str(uuid.uuid4())[0:6]}", hooks=[]
        )
    return st.session_state.burr_app


def main():
    st.title("Streaming chatbot with Burr")
    app = initialize_app()

    prompt = st.chat_input("Ask me a question!", key="chat_input")
    for chat_message in app.state.get("chat_history", []):
        render_chat_message(chat_message)

    if prompt:
        render_chat_message({"role": "user", "content": prompt, "type": "text"})
        with st.spinner(text="Waiting for response..."):
            action, streaming_container = app.stream_result(
                halt_after=chatbot_application.TERMINAL_ACTIONS, inputs={"prompt": prompt}
            )
        if action.streaming:
            render_streaming_chat_message(streaming_container)
        else:
            render_chat_message(streaming_container.get()[0]["response"])

        # for action, result, state in app.iterate(
        #     inputs={"prompt": prompt}, halt_after=["response"]
        # ):
        #     if action.name in ["prompt", "response"]:
        #         render_chat_message(result["chat_item"])


if __name__ == "__main__":
    main()
