import json
from typing import Any, Dict, Optional

import func_agent
from hamilton import driver, lifecycle
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL

from burr import core
from burr.core import Action, ApplicationBuilder, State, action, default
from burr.lifecycle import PostRunStepHook
from burr.tracking import client as burr_tclient
from burr.visibility import ActionSpanTracer, TracerFactory


class SimpleTracer(lifecycle.NodeExecutionHook):
    """Simple Hamilton Tracer"""

    def __init__(self, tracer: TracerFactory):
        self._tracer: TracerFactory = tracer
        self.active_spans = {}

    def run_before_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        task_id: Optional[str],
        run_id: str,
        node_input_types: Dict[str, Any],
        **future_kwargs: Any,
    ):
        context_manager: ActionSpanTracer = self._tracer(node_name)
        context_manager.__enter__()
        self.active_spans[node_name] = context_manager

    def run_after_node_execution(
        self,
        *,
        node_name: str,
        node_tags: Dict[str, Any],
        node_kwargs: Dict[str, Any],
        node_return_type: type,
        result: Any,
        error: Optional[Exception],
        success: bool,
        task_id: Optional[str],
        run_id: str,
        **future_kwargs: Any,
    ):
        context_manager = self.active_spans.pop(node_name)
        context_manager.__exit__(None, None, None)


def initialize_tool_dag(agent_name: str, tracer: TracerFactory) -> driver.Driver:
    tracer = SimpleTracer(tracer)
    # Initialize some things needed for tools.
    tool_dag = driver.Builder().with_modules(func_agent).with_adapters(tracer).build()
    return tool_dag


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
def chart_generator(state: State, __tracer: TracerFactory) -> tuple[dict, State]:
    query = state["query"]
    tool_dag = initialize_tool_dag("chart_generator", __tracer)
    result = tool_dag.execute(
        ["parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [python_repl],
            "system_message": "Any charts you display will be visible by the user. When done say 'FINAL ANSWER'.",
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
def researcher(state: State, __tracer: TracerFactory) -> tuple[dict, State]:
    query = state["query"]
    tool_dag = initialize_tool_dag("researcher", __tracer)
    result = tool_dag.execute(
        ["parsed_tool_calls", "llm_function_message"],
        inputs={
            "tools": [tavily_tool],
            "system_message": "You should provide accurate data for the chart generator to use. When done say 'FINAL ANSWER'.",
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
        " Once the python code has been written and the graph drawn, the task is complete.",
        "sender": "",
        "parsed_tool_calls": [],
    }, "researcher"


def main(app_instance_id: str = None, sequence_number: int = -1):
    project_name = "demo:hamilton-multi-agent-v1"
    if app_instance_id:
        state, entry_point = burr_tclient.LocalTrackingClient.load_state(
            project_name, app_instance_id, sequence_no=sequence_number
        )
    else:
        state, entry_point = default_state_and_entry_point()
    # look up app_id for particular user
    # if None -- then proceed with defaults
    # else load from state, and set entry point
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
        .with_tracker(project=project_name)
        .build()
    )
    app.visualize(
        output_file_path="hamilton-multi-agent-v2", include_conditions=True, view=True, format="png"
    )
    app.run(halt_after=["terminal"])


if __name__ == "__main__":
    # Add an app_id to restart from last sequence in that state
    # e.g. fine the ID in the UI and then put it in here "app_f0e4a918-b49c-4ee1-9d2b-30c15104c51c"
    # _app_id = None  # "app_4ed5b3b3-0f38-4b37-aed7-559d506174c7"
    _app_id = "app_4ed5b3b3-0f38-4b37-aed7-559d506174c7"
    # _sequence_no = None  # 23
    _sequence_no = 23
    main(None, None)
    # main(_app_id, _sequence_no)

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
