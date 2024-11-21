from ast import literal_eval
from typing import Tuple

import yfinance as yf

from burr.core import State, action


@action(reads=[], writes=["tool_params"])
def determine_tool(state: State, prompt: str) -> Tuple[dict, State]:
    # uses the anthropic API to choose which tool to use
    pass


@action(reads=["tool_params"], writes=["response"])
def calculator_tool(state: State) -> Tuple[dict, State]:
    # tool to perform calculations
    tool_params = state["tool_params"]
    result = literal_eval(tool_params["expression"])
    response = {
        "raw_result": "result",
        "text_response": f"The result of {tool_params['expression']} is {result}",
    }
    return {"raw_result": result, "response": response}, state.update(response=response)


@action(reads=["tool_params"], writes=["response"])
def stock_lookup_tool(state: State) -> Tuple[dict, State]:
    # tool to lookup stock prices
    tool_params = state["tool_params"]
    ticker = tool_params["ticker"]
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1d")
    current_price = hist["Close"][-1]
    return {
        "raw_result": current_price,
        "response": {
            "raw_result": current_price,
            "text_response": f"The current price of {ticker} is {current_price}",
        },
    }, state.update(
        response={
            "raw_result": current_price,
            "text_response": f"The current price of {ticker} is {current_price}",
        }
    )


@action(reads=["tool_params"], writes=["response"])
def weather_lookup_tool(state: State) -> Tuple[dict, State]:
    # tool_params = state["tool_params"]
    # city = tool_params["city"]
    # TODO -- use this to get the weather: https://pypi.org/project/openmeteo-py/0.0.1/
    pass


def fallback_tool(state: State) -> Tuple[dict, State]:
    # fallback tool
    pass
