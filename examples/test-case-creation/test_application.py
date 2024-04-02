"""
This is an example test module showing how you can test an action in your application.

1. There is a very straightforward unit testing style approach.
2. There is a more sophisticated approach that uses pytest_generate_tests to dynamically generate test cases.
To use this approach you need to do `from burr.testing import pytest_generate_tests  # noqa: F401`.

"""
import pytest
from application import prompt_for_more

from burr.core import state

# the following is required to run file based tests
from burr.testing import pytest_generate_tests  # noqa: F401


def test_prompt_for_more():
    """A basic test showing how to 'unit' test an action."""
    # set up state to pass in
    input_state = state.State(
        {
            "prompt": "",
            "chat_history": [],
        }
    )
    # Set up expected result and output state
    expected_state = state.State(
        {
            "prompt": "",
            "chat_history": [],
            "response": {
                "content": "None of the response modes I support apply to your question. Please clarify?",
                "type": "text",
                "role": "assistant",
            },
        }
    )
    result, output_state = prompt_for_more(input_state)
    # evaluate the output
    # TODO: choose appropriate way to evaluate the output based on your needs.
    # e.g. exact match, fuzzy match, LLM grade, etc.
    assert output_state == expected_state
    assert result == {
        "response": {
            "content": "None of the response modes I support apply to your question. Please clarify?",
            "type": "text",
            "role": "assistant",
        }
    }


@pytest.mark.file_name("prompt_for_more.json")
def test_prompt_for_more_from_file(input_state, expected_state):
    """Function for testing the action"""
    input_state = state.State(input_state)
    expected_state = state.State(expected_state)
    _, output_state = prompt_for_more(input_state)  # exercising the action
    # TODO: choose appropriate way to evaluate the output
    # e.g. exact match, fuzzy match, LLM grade, etc.
    # this is exact match here on all values in state
    assert output_state == expected_state
    # for output that varies, you can do something like this
    # assert 'some value' in output_state["response"]["content"]
    # or, have an LLM Grade things -- you need to create the llm_evaluator function:
    # assert llm_evaluator("are these two equivalent responses. Respond with Y for yes, N for no",
    # output_state["response"]["content"], expected_state["response"]["content"]) == "Y"
