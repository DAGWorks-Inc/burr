import asyncio
import logging
import uuid

import application as chatbot_application
import streamlit as st
from hamilton.log_setup import setup_logging

import burr.core
from burr.core.action import AsyncStreamingResultContainer

setup_logging(logging.INFO)


def render_chat_message(chat_item: dict):
    content = chat_item["content"]
    role = chat_item["role"]
    with st.chat_message(role):
        st.write(content)


async def render_streaming_chat_message(stream: AsyncStreamingResultContainer):
    buffer = ""
    with st.chat_message("assistant"):
        # This is very ugly as streamlit does not support async generators
        # Thus we have to ignore the benefit of writing the delta and instead write *everything*
        with st.empty():
            async for item in stream:
                buffer += item["delta"]
                st.write(buffer)


def initialize_app() -> burr.core.Application:
    if "burr_app" not in st.session_state:
        st.session_state.burr_app = chatbot_application.application(
            app_id=f"chat_streaming:{str(uuid.uuid4())[0:6]}"
        )
    return st.session_state.burr_app


async def main():
    st.title("Streaming chatbot with Burr")
    app = initialize_app()

    prompt = st.chat_input("Ask me a question!", key="chat_input")
    for chat_message in app.state.get("chat_history", []):
        render_chat_message(chat_message)

    if prompt:
        render_chat_message({"role": "user", "content": prompt, "type": "text"})
        with st.spinner(text="Waiting for response..."):
            action, streaming_container = await app.astream_result(
                halt_after=chatbot_application.TERMINAL_ACTIONS, inputs={"prompt": prompt}
            )
        await render_streaming_chat_message(streaming_container)


if __name__ == "__main__":
    asyncio.run(main())
