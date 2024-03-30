"""
This is an example test module showing how you can test an action in your application.

1. There is a very straightforward unit testing style approach.
2. There is a more complex approach that uses pytest_generate_tests to dynamically generate test cases.
"""
import json

import pytest
from application import prompt_for_more

from burr.core import state


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


# one way to parameterize tests is to store the serialized state in a json file
# and then load it for the test.
def load_test_cases(file_name: str) -> tuple:
    """Load test cases from a json file."""
    with open(file_name, "r") as f:
        json_test_cases = json.load(f)
        test_cases = [(tc.get("input_state"), tc.get("expected_state")) for tc in json_test_cases]
        test_ids = [
            f"{tc.get('action', 'ACTION_MISSING')}-{tc.get('name', 'NAME_MISSING')}"
            for tc in json_test_cases
        ]
    return test_cases, test_ids


# Define the pytest_generate_tests hook to generate test cases dynamically based on the
# contents of a file
def pytest_generate_tests(metafunc):
    """This function dynamically generates test cases based on the contents of a file."""

    # for each function that has the 'input_state' and 'expected_state' arguments:
    if "input_state" in metafunc.fixturenames and "expected_state" in metafunc.fixturenames:
        # gets all filenames from the 'file_name' marker
        file_names = [
            file_arg
            for m in metafunc.definition.own_markers
            if m.name == "file_name"
            for file_arg in m.args
        ]
        all_test_cases = []
        all_test_ids = []
        for file_name in file_names:
            test_cases, test_case_ids = load_test_cases(file_name)
            all_test_cases.extend(test_cases)
            all_test_ids.extend(test_case_ids)
        if not all_test_cases:
            raise ValueError(
                f"No test cases could be created for test {metafunc.definition.originalname}."
            )
        # Generate test cases based on the test_data list
        metafunc.parametrize("input_state,expected_state", all_test_cases, ids=all_test_ids)


@pytest.mark.file_name("prompt_for_more.json")
def test_prompt_for_more_from_file(input_state, expected_state):
    """Function for testing the action"""
    input_state = state.State(input_state)
    expected_state = state.State(expected_state)
    _, output_state = prompt_for_more(input_state)  # exercising the action
    assert output_state == expected_state
