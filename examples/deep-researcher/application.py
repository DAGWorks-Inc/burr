import openai
import json

from burr.core import action, State, ApplicationBuilder, expr, when
from prompts import (
    query_writer_instructions, summarizer_instructions, reflection_instructions
)
from utils import deduplicate_and_format_sources, tavily_search, format_sources


def query_openai(system_instructions, human_message_content, stream=False):
    """
    Sends a query to the OpenAI API and retrieves the response.

    Args:
        system_instructions (str): Instructions for the system message.
        human_message_content (str): Content of the human message.
        stream (bool, optional): Whether to stream the response. Defaults to False.

    Returns:
        str: The content of the response from the OpenAI API.
    """
    client = openai.Client()
    system_message = {'role': 'system', 'content': system_instructions}
    human_message = {'role': 'user', 'content': human_message_content}
    messages = []
    messages.append(system_message)
    messages.append(human_message)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        stream=stream
    )
    content = response.choices[0].message.content
    return content


@action(reads=["research_topic"], writes=["search_query"])
def generate_query(state: State) -> State:
    """
    Generates a search query based on the research topic.

    Args:
        state (State): The current application state.

    Returns:
        State: The updated state with the generated search query.
    """
    research_topic = state['research_topic']
    system_prompt_formatted = query_writer_instructions.format(research_topic=research_topic)
    human_prompt = "Generate a query for web search:"
    my_query = query_openai(system_prompt_formatted, human_prompt)
    as_dict = json.loads(my_query)
    return state.update(search_query=as_dict['query'])


@action(reads=["search_query", "research_loop_count"], writes=["sources_gathered", "research_loop_count", "web_research_results"])
def web_research(state: State) -> State:
    """
    Performs web research based on the search query and updates the state.

    Args:
        state (State): The current application state.

    Returns:
        State: The updated state with gathered sources, research loop count, and web research results.
    """
    search_results = tavily_search(
        state['search_query'], include_raw_content=True, max_results=1
    )
    search_str = deduplicate_and_format_sources(
        search_results, max_tokens_per_source=1000, include_raw_content=True)
    sources_gathered = [format_sources(search_results)]
    research_loop_count = state['research_loop_count'] + 1
    web_research_results = [search_str]
    return state.update(sources_gathered=sources_gathered, research_loop_count=research_loop_count, web_research_results=web_research_results)


@action(reads=["running_summary", "web_research_results", "research_topic"], writes=["running_summary"])
def summarize_sources(state: State):
    """
    Summarizes the gathered sources and updates the running summary.

    Args:
        state (State): The current application state.

    Returns:
        State: The updated state with the new running summary.
    """
    existing_summary = state['running_summary']
    most_recent_web_research = state['web_research_results'][-1]
    research_topic = state['research_topic']

    if existing_summary:
        human_message_content = (
            f"<User Input> \n {research_topic} \n <User Input>\n\n"
            f"<Existing Summary> \n {existing_summary} \n <Existing Summary>\n\n"
            f"<New Search Results> \n {most_recent_web_research} \n <New Search Results>"
        )
    else:
        human_message_content = (
            f"<User Input> \n {research_topic} \n <User Input>\n\n"
            f"<Search Results> \n {most_recent_web_research} \n <Search Results>"
        )
    running_summary = query_openai(summarizer_instructions, human_message_content)

    while "<think>" in running_summary and "</think>" in running_summary:
        start = running_summary.find("<think>")
        end = running_summary.find("</think>") + len("</think>")
        running_summary = running_summary[:start] + running_summary[end:]
    return state.update(running_summary=running_summary)


@action(reads=["running_summary", "research_topic"], writes=["search_query"])
def reflect_on_summary(state: State):
    """
    Reflects on the running summary to identify knowledge gaps and generate a follow-up query.

    Args:
        state (State): The current application state.

    Returns:
        State: The updated state with the follow-up search query.
    """
    system_instructions = reflection_instructions.format(
        research_topic=state.get('research_topic')
    )
    human_message_content = f"Identify a knowledge gap and generate a follow-up web search query based on our existing knowledge: {state.get('running_summary')}"
    content = query_openai(system_instructions, human_message_content)
    follow_up_query = json.loads(content)

    query = follow_up_query.get("follow_up_query")
    if not query:
        fallback_query = f"Tell me more about {state.get('research_topic')}"
        state.update(search_query=fallback_query)
    return state.update(search_query=query)


@action(reads=["running_summary", "sources_gathered"], writes=["running_summary"])
def finalize_summary(state: State):
    """
    Finalizes the summary by combining the running summary and all gathered sources.

    Args:
        state (State): The current application state.

    Returns:
        State: The updated state with the finalized summary.
    """
    all_sources = "\n".join(source for source in state.get('sources_gathered'))
    running_summary = (
        f"## Summary\n\n{state.get('running_summary')}\n\n ### Sources:\n{all_sources}"
    )
    return state.update(running_summary=running_summary)


if __name__ == "__main__":
    """
    Entry point for the application. Initializes the research topic and runs the application.
    """
    research_topic = "getting a job in datascience"
    project_name = "RESEARCH_ASSISTANT"
    app_id = "4"
    num_loops = 2

    app = (
        ApplicationBuilder()
        .with_actions(generate_query, web_research, summarize_sources, reflect_on_summary, finalize_summary)
        .with_transitions(
            ("generate_query", "web_research"),
            ("web_research", "summarize_sources"),
            ("summarize_sources", "reflect_on_summary"),
            ("reflect_on_summary", "finalize_summary", when(research_loop_count=num_loops)),
            ("reflect_on_summary", "web_research", expr(f'research_loop_count<{num_loops}'))
        )
        .with_state(research_loop_count=0, research_topic=research_topic, running_summary=None)
        .with_tracker(project=project_name)
        .with_identifiers(app_id=app_id)
        .with_entrypoint("generate_query")
        .build()
    )
    *_, state = app.run(halt_after=["finalize_summary"])
    print(app.state["running_summary"])
