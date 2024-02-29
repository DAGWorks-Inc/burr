import json
from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.tool_executor import ToolExecutor, ToolInvocation

from burr import core
from burr.core import Action, State, action, default, expr
from burr.lifecycle import PostRunStepHook
from burr.tracking import client as burr_tclient

tavily_tool = TavilySearchResults(max_results=5)

# Warning: This executes code locally, which can be unsafe when not sandboxed

repl = PythonREPL()


def create_agent(llm, tools, system_message: str):
    """Helper function to create an agent with a system message and tools."""
    functions = [convert_to_openai_function(t) for t in tools]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_functions(functions)


@tool
def python_repl(code: Annotated[str, "The python code to execute to generate your chart."]):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return f"Succesfully executed:\n```python\n{code}\n```\nStdout: {result}"


# Helper function to create a node for a given agent
def _agent_node(messages: list, sender: str, agent, name: str) -> dict:
    result = agent.invoke({"messages": messages, "sender": sender})
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, FunctionMessage):
        pass
    else:
        result = HumanMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": result,
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }


# Objects for the agents
llm = ChatOpenAI(model="gpt-4-1106-preview")
research_agent = create_agent(
    llm,
    [tavily_tool],
    system_message="You should provide accurate data for the chart generator to use.",
)
chart_agent = create_agent(
    llm,
    [python_repl],
    system_message="Any charts you display will be visible by the user.",
)


@action(reads=["messages", "sender"], writes=["messages", "sender"])
def research_node(state: State) -> tuple[dict, State]:
    # Research agent and node
    result = _agent_node(state["messages"], state["sender"], research_agent, "Researcher")
    return result, state.append(messages=result["messages"]).update(sender="Researcher")


@action(reads=["messages", "sender"], writes=["messages", "sender"])
def chart_node(state: State) -> tuple[dict, State]:
    result = _agent_node(state["messages"], state["sender"], chart_agent, "Chart Generator")
    return result, state.append(messages=result["messages"]).update(sender="Chart Generator")


tools = [tavily_tool, python_repl]
tool_executor = ToolExecutor(tools)


@action(reads=["messages"], writes=["messages"])
def tool_node(state: State) -> tuple[dict, State]:
    """This runs tools in the graph

    It takes in an agent action and calls that tool and returns the result."""
    messages = state["messages"]
    # Based on the continue condition
    # we know the last message involves a function call
    last_message = messages[-1]
    # We construct an ToolInvocation from the function_call
    tool_input = json.loads(last_message.additional_kwargs["function_call"]["arguments"])
    # We can pass single-arg inputs by value
    if len(tool_input) == 1 and "__arg1" in tool_input:
        tool_input = next(iter(tool_input.values()))
    tool_name = last_message.additional_kwargs["function_call"]["name"]
    action = ToolInvocation(
        tool=tool_name,
        tool_input=tool_input,
    )
    # We call the tool_executor and get back a response
    response = tool_executor.invoke(action)
    # We use the response to create a FunctionMessage
    function_message = FunctionMessage(
        content=f"{tool_name} response: {str(response)}", name=action.tool
    )
    # We return a list, because this will get added to the existing list
    return {"messages": [function_message]}, state.append(messages=function_message)


@action(reads=[], writes=[])
def terminal_step(state: State) -> tuple[dict, State]:
    return {}, state


class PrintStepHook(PostRunStepHook):
    def post_run_step(self, *, state: "State", action: "Action", **future_kwargs):
        print("action=====\n", action)
        print("state======\n", state)


def default_state_and_entry_point() -> tuple[dict, str]:
    return (
        dict(
            messages=[
                HumanMessage(
                    content="Fetch the UK's GDP over the past 5 years,"
                    " then draw a line graph of it."
                    " Once you code it up, finish."
                )
            ],
            sender=None,
        ),
        "researcher",
    )


def main(app_instance_id: str = None):
    project_name = "demo:hamilton-multi-agent"
    if app_instance_id:
        initial_state, entry_point = burr_tclient.LocalTrackingClient.get_state(
            project_name, app_instance_id
        )
        # TODO: rehydrate langchain objects from JSON
    else:
        initial_state, entry_point = default_state_and_entry_point()
    app = (
        core.ApplicationBuilder()
        .with_state(**initial_state)
        .with_actions(
            researcher=research_node,
            charter=chart_node,
            call_tool=tool_node,
            terminal=terminal_step,
        )
        .with_transitions(
            ("researcher", "call_tool", expr("'function_call' in messages[-1].additional_kwargs")),
            ("researcher", "terminal", expr("'FINAL ANSWER' in messages[-1].content")),
            ("researcher", "charter", default),
            ("charter", "call_tool", expr("'function_call' in messages[-1].additional_kwargs")),
            ("charter", "terminal", expr("'FINAL ANSWER' in messages[-1].content")),
            ("charter", "researcher", default),
            ("call_tool", "researcher", expr("sender == 'Researcher'")),
            ("call_tool", "charter", expr("sender == 'Chart Generator'")),
        )
        .with_entrypoint(entry_point)
        .with_hooks(PrintStepHook())
        .with_tracker("demo:lcel-multi-agent")
        .build()
    )
    app.visualize(
        output_file_path="lcel-multi-agent", include_conditions=True, view=True, format="png"
    )
    app.run(halt_after=["terminal"])


if __name__ == "__main__":
    main()
    # main(SOME_APP_ID)  # use this to restart from a previous state
