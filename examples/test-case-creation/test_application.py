"""
This is an example test module showing how you can test an action in your application.

1. There is a very straightforward unit testing style approach.
2. There is a more complex approach that uses pytest_generate_tests to dynamically generate test cases.
To use this approach you need to do `from burr.testing import pytest_generate_tests  # noqa: F401 `
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
    # evaluate
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
    assert output_state == expected_state
