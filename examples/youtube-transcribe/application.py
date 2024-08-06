import pprint

import openai
from dataflows import generative, ingestion, retrieval
from hamilton import driver

from burr.core import ApplicationBuilder, Result, State, action


@action(
    reads=["chat_history"],
    writes=["chat_history"],
)
def bot_turn(state: State, rag_driver: driver.Driver, llm_client: openai.OpenAI, user_input: str):
    # NOTE about explicit LLM state management. By default local LLMs maintain the chat history on the
    # server. Therefore, if the client explicitly pass the chat history too, it will grow exponentially.
    chat_history = state["chat_history"]

    # retrieve information and augment the user prompt with it.
    context_results = rag_driver.execute(
        ["response_prompt"], inputs=dict(search_input=user_input, top_k=5)
    )
    user_input_with_context = context_results["response_prompt"]

    # overwrite chat history (can't remember why I do that, might be an error)
    messages = chat_history[:-1] + [dict(role="user", content=user_input_with_context)]

    # generative
    # specify model for OpenAI, pass empty string for local LLM
    response = llm_client.chat.completions.create(model=..., messages=messages)
    content = response.choices[0].message.content

    # a 2nd RAG step. Instead of opening the context provided to the LLM
    # we open the resources most relevant to the generated answer
    resource_results = rag_driver.execute(
        ["open_resource", "selected_result"], inputs=dict(search_input=content, top_k=1)
    )

    results = {
        "content": content,
        "messages": response.choices,
        "resource": resource_results["selected_result"],
    }
    return results, state.append(chat_history=dict(role="assistant", content=content))


def build_application():
    rag_driver = driver.Builder().with_modules(ingestion, retrieval, generative).build()
    # set API key for OpenAI, set base_url for local LLM
    llm_client = openai.OpenAI(api_key=..., base_url=...)

    return (
        ApplicationBuilder()
        .with_actions(
            bot_turn.bind(rag_driver=rag_driver, llm_client=llm_client),
            exit=Result("chat_history"),
        )
        .with_transitions(("bot_turn", "bot_turn"))
        .with_entrypoint("bot_turn")
        .with_tracker("local", project="rag_bot")
        .build()
    )


def main():
    app = build_application()

    user_input = None
    while True:
        previous_action, result, _ = app.run(
            halt_before=["bot_turn"],
            inputs={"user_input": user_input},
        )
        user_input = input("User: ")
        if previous_action.name == "exit":
            # reached the end
            pprint.pprint(result)
            return


if __name__ == "__main__":
    main()
