import json
import os.path

import func_agent
from hamilton import driver
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL

from burr import core
from burr.core import Action, ApplicationBuilder, State
from burr.core.action import action
from burr.lifecycle import PostRunStepHook

# @action(reads=["code"], writes=["code_result"])
# def run_code(state: State) -> tuple[dict, State]:
#     _code = state["code"]
#     try:
#         result = repl.run(_code)
#     except BaseException as e:
#         _code_result = {"status": "error", "result": f"Failed to execute. Error: {repr(e)}"
#         return {"result": f"Failed to execute. Error: {repr(e)}"}, state.update(code_result=_code_result)
#     _code_result = {"status": "success", "result": result}
#     return {"status": "success", "result": result}, state.update(code_result=_code_result)
#
# @action(reads=["code"], writes=["code_result"])
# def run_tavily(state: State) -> tuple[dict, State]:
#     _code = state["code"]
#     try:
#         result = repl.run(_code)
#     except BaseException as e:
#         _code_result = {"status": "error", "result": f"Failed to execute. Error: {repr(e)}"
#         return {"result": f"Failed to execute. Error: {repr(e)}"}, state.update(code_result=_code_result)
#     _code_result = {"status": "success", "result": result}
#     return {"status": "success", "result": result}, state.update(code_result=_code_result)


tool_dag = driver.Builder().with_modules(func_agent).build()

repl = PythonREPL()


def python_repl(code: str) -> dict:
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user.

    :param code: string. The python code to execute.
    :return: the output
    """
    try:
        result = repl.run(code)
    except BaseException as e:
        return {"error": repr(e), "status": "error"}
    return {"status": "success", "code": f"```python\n{code}\n```", "Stdout": result}


@action(reads=["query", "messages"], writes=["messages", "next_hop"])
def chart_generator(state: State) -> tuple[dict, State]:
    query = state["query"]
    result = tool_dag.execute(
        ["executed_tool_calls", "parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [python_repl],
            "system_message": "Any charts you display will be visible by the user.",
            "user_query": query,
            "messages": state["messages"],
        },
    )
    # _code = result["parsed_tool_calls"][0]["function_args"]["code"]
    new_messages = [result["llm_function_message"]]
    for tool_name, tool_result in result["executed_tool_calls"]:
        new_messages.append(tool_result)
    if len(new_messages) == 1:
        if new_messages[0]["content"] and "FINAL ANSWER" in new_messages[0]["content"]:
            next_hop = "complete"
        else:
            next_hop = "continue"
    else:
        # assess tool results
        next_hop = "self"
    state = state.update(next_hop=next_hop)
    for message in new_messages:
        state = state.append(messages=message)
    return result, state


tavily_tool = TavilySearchResults(max_results=5)


@action(reads=["query", "messages"], writes=["messages", "next_hop"])
def researcher(state: State) -> tuple[dict, State]:
    query = state["query"]
    result = tool_dag.execute(
        ["executed_tool_calls", "parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [tavily_tool],
            "system_message": "You should provide accurate data for the chart generator to use.",
            "user_query": query,
            "messages": state["messages"],
        },
    )
    new_messages = [result["llm_function_message"]]
    for tool_name, tool_result in result["executed_tool_calls"]:
        new_messages.append(tool_result)
    if len(new_messages) == 1:
        if "FINAL ANSWER" in new_messages[0]["content"]:
            next_hop = "complete"
        else:
            next_hop = "continue"
    else:
        # assess tool results
        next_hop = "self"
    state = state.update(next_hop=next_hop)
    for message in new_messages:
        state = state.append(messages=message)
    return result, state


@action(reads=[], writes=[])
def terminal_step(state: State) -> tuple[dict, State]:
    return {}, state


class PrintStepHook(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        print("action=====\n", action)
        print("state======\n", state)


def initialize_state_from_logs(tracker_name: str, app_id: str) -> tuple[dict, str]:
    """Initialize the state to debug from an exception

    :param tracker_name:
    :param app_id:
    :return:
    """
    # open ~/.burr/{tracker_name}/{app_id}/log.jsonl
    # find the first entry with an exception -- and pull state from it.
    with open(f"{os.path.expanduser('~/')}/.burr/{tracker_name}/{app_id}/log.jsonl", "r") as f:
        lines = f.readlines()
    for line in lines:
        line = json.loads(line)
        if "exception" in line:
            state = line["state"]
            entry_point = line["action"]
            return state, entry_point
    raise ValueError(f"No exception found in logs for {tracker_name}/{app_id}")


def default_state_and_entry_point() -> tuple[dict, str]:
    return {
        "messages": [],
        "query": "Fetch the UK's GDP over the past 5 years,"
        " then draw a line graph of it."
        " Once you code it up, finish.",
        "next_hop": "",
    }, "researcher"


def main(app_instance_id: str = None):
    tracker_name = "hamilton-multi-agent"
    if app_instance_id:
        state, entry_point = initialize_state_from_logs(tracker_name, app_instance_id)
    else:
        state, entry_point = default_state_and_entry_point()

    app = (
        ApplicationBuilder()
        .with_state(**state)
        .with_actions(
            researcher=researcher,
            chart_generator=chart_generator,
            terminal=terminal_step,
        )
        .with_transitions(
            ("researcher", "researcher", core.expr("next_hop == 'self'")),
            ("researcher", "chart_generator", core.expr("next_hop == 'continue'")),
            ("chart_generator", "chart_generator", core.expr("next_hop == 'self'")),
            ("chart_generator", "researcher", core.expr("next_hop == 'continue'")),
            (
                "researcher",
                "terminal",
                core.expr("next_hop == 'complete'"),
            ),  # core.expr("'FINAL ANSWER' in messages[-1]['content']")),
            (
                "chart_generator",
                "terminal",
                core.expr("next_hop == 'complete'"),
            ),  # core.expr("'FINAL ANSWER' in messages[-1]['content']")),
        )
        .with_entrypoint(entry_point)
        .with_hooks(PrintStepHook())
        .with_tracker(tracker_name)
        .build()
    )
    app.run(halt_after=["terminal"])
    # return app


if __name__ == "__main__":
    _app_id = "app_4d1618d2-79d1-4d89-8e3f-70c216c71e63"
    main(_app_id)
    import sys

    sys.exit(0)
    """TODO:
    1. need to figure out the messages state.
    2. the current design is each DAG run also calls the tool.
    3. so need to then update messages history appropriately
    so that the "agents" can iterate until they are done.

    Note: https://github.com/langchain-ai/langgraph/blob/main/examples/multi_agent/multi-agent-collaboration.ipynb
    Is a little messy to figure out. So best to approach from first
    principles what is actually going on.

    """
    repl = PythonREPL()
    tavily_tool = TavilySearchResults(max_results=5)
    result = tool_dag.execute(
        ["executed_tool_calls"],
        inputs={
            "tools": [tavily_tool],
            "system_message": "You should provide accurate data for the chart generator to use.",
            "user_query": "Fetch the UK's GDP over the past 5 years,"
            " then draw a line graph of it."
            " Once you have written code for the graph, finish.",
        },
    )
    import pprint

    pprint.pprint(result)

    result = tool_dag.execute(
        ["executed_tool_calls"],
        inputs={
            "tools": [python_repl],
            "system_message": "Any charts you display will be visible by the user.",
            "user_query": "Draw a simple line graph of y = x",
        },
    )
    import pprint

    pprint.pprint(result)
