import json

import func_agent
from hamilton import driver
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL

from burr import core
from burr.core import Action, ApplicationBuilder, State, action, default
from burr.lifecycle import PostRunStepHook
from burr.tracking import client as burr_tclient

# Initialize some things needed for tools.
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
        return {"error": repr(e), "status": "error", "code": f"```python\n{code}\n```"}
    return {"status": "success", "code": f"```python\n{code}\n```", "Stdout": result}


@action(reads=["query", "messages"], writes=["messages", "next_hop"])
def chart_generator(state: State) -> tuple[dict, State]:
    query = state["query"]
    result = tool_dag.execute(
        ["parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [python_repl],
            "system_message": "Any charts you display will be visible by the user.",
            "user_query": query,
            "messages": state["messages"],
        },
    )
    # _code = result["parsed_tool_calls"][0]["function_args"]["code"]
    new_message = result["llm_function_message"]
    parsed_tool_calls = result["parsed_tool_calls"]
    state = state.update(parsed_tool_calls=parsed_tool_calls)
    state = state.append(messages=new_message)
    state = state.update(sender="chart_generator")
    return result, state


tavily_tool = TavilySearchResults(max_results=5)


@action(reads=["query", "messages"], writes=["messages", "next_hop"])
def researcher(state: State) -> tuple[dict, State]:
    query = state["query"]
    result = tool_dag.execute(
        ["parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [tavily_tool],
            "system_message": "You should provide accurate data for the chart generator to use.",
            "user_query": query,
            "messages": state["messages"],
        },
    )
    new_message = result["llm_function_message"]
    parsed_tool_calls = result["parsed_tool_calls"]
    state = state.update(parsed_tool_calls=parsed_tool_calls)
    state = state.append(messages=new_message)
    state = state.update(sender="researcher")
    return result, state


tools = [tavily_tool, python_repl]


@action(reads=["messages", "parsed_tool_calls"], writes=["messages", "parsed_tool_calls"])
def tool_node(state: State) -> tuple[dict, State]:
    """This runs tools in the graph

    It takes in an agent action and calls that tool and returns the result."""
    new_messages = []
    parsed_tool_calls = state["parsed_tool_calls"]

    for tool_call in parsed_tool_calls:
        tool_name = tool_call["function_name"]
        tool_args = tool_call["function_args"]
        tool_found = False
        for tool in tools:
            name = getattr(tool, "name", None)
            if name is None:
                name = tool.__name__
            if name == tool_name:
                tool_found = True
                kwargs = json.loads(tool_args)
                if hasattr(tool, "_run"):
                    result = tool._run(**kwargs)
                else:
                    result = tool(**kwargs)
                # str_result = str(result)
                new_messages.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": tool_name,
                        "content": result,
                    }
                )
        if not tool_found:
            raise ValueError(f"Tool {tool_name} not found.")

    for tool_result in new_messages:
        state = state.append(messages=tool_result)
    state = state.update(parsed_tool_calls=[])
    # We return a list, because this will get added to the existing list
    return {"messages": new_messages}, state


@action(reads=[], writes=[])
def terminal_step(state: State) -> tuple[dict, State]:
    return {}, state


class PrintStepHook(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        print("action=====\n", action)
        print("state======\n", state)


def default_state_and_entry_point() -> tuple[dict, str]:
    return {
        "messages": [],
        "query": "Fetch the UK's GDP over the past 5 years,"
        " then draw a line graph of it."
        " Once you code it up, finish.",
        "sender": "",
        "parsed_tool_calls": [],
    }, "researcher"


def main(app_instance_id: str = None):
    project_name = "demo:hamilton-multi-agent-v1"
    if app_instance_id:
        state, entry_point = burr_tclient.LocalTrackingClient.load_state(
            project_name, app_instance_id
        )
    else:
        state, entry_point = default_state_and_entry_point()

    app = (
        ApplicationBuilder()
        .with_state(**state)
        .with_actions(
            researcher=researcher,
            chart_generator=chart_generator,
            tool_node=tool_node,
            terminal=terminal_step,
        )
        .with_transitions(
            ("researcher", "tool_node", core.expr("len(parsed_tool_calls) > 0")),
            (
                "researcher",
                "terminal",
                core.expr("'FINAL ANSWER' in messages[-1]['content']"),
            ),
            ("researcher", "chart_generator", default),
            ("chart_generator", "tool_node", core.expr("len(parsed_tool_calls) > 0")),
            (
                "chart_generator",
                "terminal",
                core.expr("'FINAL ANSWER' in messages[-1]['content']"),
            ),
            ("chart_generator", "researcher", default),
            ("tool_node", "researcher", core.expr("sender == 'researcher'")),
            ("tool_node", "chart_generator", core.expr("sender == 'chart_generator'")),
        )
        .with_entrypoint(entry_point)
        .with_hooks(PrintStepHook())
        .with_tracker(project_name)
        .build()
    )
    app.visualize(
        output_file_path="hamilton-multi-agent-v2", include_conditions=True, view=True, format="png"
    )
    app.run(halt_after=["terminal"])


if __name__ == "__main__":
    # Add an app_id to restart from last sequence in that state
    # e.g. fine the ID in the UI and then put it in here "app_f0e4a918-b49c-4ee1-9d2b-30c15104c51c"
    _app_id = None  # "app_fb52ca3b-9198-4e5a-9ee0-9c07df1d7edd"
    main(_app_id)

    # some test code
    # tavily_tool = TavilySearchResults(max_results=5)
    # result = tool_dag.execute(
    #     ["executed_tool_calls"],
    #     inputs={
    #         "tools": [tavily_tool],
    #         "system_message": "You should provide accurate data for the chart generator to use.",
    #         "user_query": "Fetch the UK's GDP over the past 5 years,"
    #         " then draw a line graph of it."
    #         " Once you have written code for the graph, finish.",
    #     },
    # )
    # import pprint
    #
    # pprint.pprint(result)
    #
    # result = tool_dag.execute(
    #     ["executed_tool_calls"],
    #     inputs={
    #         "tools": [python_repl],
    #         "system_message": "Any charts you display will be visible by the user.",
    #         "user_query": "Draw a simple line graph of y = x",
    #     },
    # )
    # import pprint
    #
    # pprint.pprint(result)
