import inspect
import json
import os
from typing import Callable, Optional

import openai
import requests

from burr.core import State, action, when
from burr.core.application import ApplicationBuilder


@action(reads=[], writes=["query"])
def process_input(state: State, query: str) -> State:
    """Simple action to process input for the assistant."""
    return state.update(query=query)


# All the tools are functions below
# They have parameters (given by their annotations), and return a dictionary
# This dictionary is free-form -- it will be interpreted by the LLM later
# In your implementation you may want to change the return type to be more specific and use it programmatically
# But for the case of a generic assistant, this is a nice way to exrpess it
def _weather_tool(latitude: float, longitude: float) -> dict:
    """Queries the weather for a given latitude and longitude."""
    api_key = os.environ.get("TOMORROW_API_KEY")
    url = f"https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&apikey={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to get weather data. Status code: {response.status_code}"}


def _text_wife_tool(message: str) -> dict:
    """Texts your wife with a message."""
    # Dummy implementation for the text wife tool
    # Replace this with actual SMS API logic
    return {"action": f"Texted wife: {message}"}


def _order_coffee_tool(
    size: str, coffee_preparation: str, any_modifications: Optional[str] = None
) -> dict:
    """Orders a coffee with the given size, preparation, and any modifications."""
    # Dummy implementation for the order coffee tool
    # Replace this with actual coffee shop API logic
    return {
        "action": (
            f"Ordered a {size} {coffee_preparation}" + "with {any_modifications}"
            if any_modifications
            else ""
        )
    }


def _fallback(response: str) -> dict:
    """Tells the user that the assistant can't do that -- this should be a fallback"""
    return {"response": response}


# You'll want to add more types here as needed

TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}

# You can also consider using a library like pydantic to further integrate with OpenAI
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": fn_name,
            "description": fn.__doc__ or fn_name,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": TYPE_MAP.get(param.annotation)
                        or "string",  # TODO -- add error cases
                        "description": param.name,
                    }
                    for param in inspect.signature(fn).parameters.values()
                },
                "required": [param.name for param in inspect.signature(fn).parameters.values()],
            },
        },
    }
    for fn_name, fn in {
        "query_weather": _weather_tool,
        "order_coffee": _order_coffee_tool,
        "text_wife": _text_wife_tool,
        "fallback": _fallback,
    }.items()
]


@action(reads=["query"], writes=["tool_parameters", "tool"])
def select_tool(state: State) -> State:
    """Selects the tool + assigns the parameters. Uses the tool-calling API."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the supplied tools to assist the user, if they apply in any way. Remember to use the tools! They can do stuff you can't."
                "If you can't use only the tools provided to answer the question but know the answer, please provide the answer"
                "If you cannot use the tools provided to answer the question, use the fallback tool and provide a reason. "
                "Again, if you can't use one tool provided to answer the question, use the fallback tool and provide a reason. "
                "You must select exactly one tool no matter what, filling in every parameters with your best guess. Do not skip out on parameters!"
            ),
        },
        {"role": "user", "content": state["query"]},
    ]
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=OPENAI_TOOLS,
    )

    # Extract the tool name and parameters from OpenAI's response
    if response.choices[0].message.tool_calls is None:
        return state.update(
            tool="fallback",
            tool_parameters={
                "response": "No tool was selected, instead response was: {response.choices[0].message}."
            },
        )
    fn = response.choices[0].message.tool_calls[0].function

    return state.update(tool=fn.name, tool_parameters=json.loads(fn.arguments))


@action(reads=["tool_parameters"], writes=["raw_response"])
def call_tool(state: State, tool_function: Callable) -> State:
    """Action to call the tool. This will be bound to the tool function."""
    response = tool_function(**state["tool_parameters"])
    return state.update(raw_response=response)


@action(reads=["query", "raw_response"], writes=["final_output"])
def format_results(state: State) -> State:
    """Action to format the results in a usable way. Note we're not cascading in context for the chat history.
    This is largely due to keeping it simple, but you'll likely want to pass IDs around or maintain the chat history yourself
    """
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Your goal is to take the"
                    "data presented and use it to answer the original question:"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"The original question was: {state['query']}."
                    f"The data is: {state['raw_response']}. Please format"
                    "the data and provide a response that responds to the original query."
                    "As always, be concise (tokens aren't free!)."
                ),
            },
        ],
    )

    return state.update(final_output=response.choices[0].message.content)


def application():
    """Builds an application"""
    return (
        ApplicationBuilder()
        .with_actions(
            process_input,
            select_tool,
            format_results,
            query_weather=call_tool.bind(tool_function=_weather_tool),
            text_wife=call_tool.bind(tool_function=_text_wife_tool),
            order_coffee=call_tool.bind(tool_function=_order_coffee_tool),
            fallback=call_tool.bind(tool_function=_fallback),
        )
        .with_transitions(
            ("process_input", "select_tool"),
            ("select_tool", "query_weather", when(tool="query_weather")),
            ("select_tool", "text_wife", when(tool="text_wife")),
            ("select_tool", "order_coffee", when(tool="order_coffee")),
            ("select_tool", "fallback", when(tool="fallback")),
            (["query_weather", "text_wife", "order_coffee", "fallback"], "format_results"),
            ("format_results", "process_input"),
        )
        .with_entrypoint("process_input")
        .with_tracker(project="demo_tool_calling", use_otel_tracing=True)
        .build()
    )


if __name__ == "__main__":
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    OpenAIInstrumentor().instrument()
    app = application()
    app.visualize(output_file_path="./statemachine.png")
    action, result, state = app.run(
        halt_after=["format_results"],
        inputs={"query": "What's the weather like in San Francisco?"},
    )
    print(state["final_output"])
