# Using Pytest to evaluate your agent / application

An agent is a combination of LLM calls and logic. But how do we know if it's working? Well we can test & evaluate it.

From a high level we want to test & evaluate the "micro" i.e. the LLM calls & individual bits of logic,
through to the "macro" i.e. the agent as a whole.

We can do this with Pytest.

## Pytest Constructs

We use the `pytest-harvest` plugin to log what our tests are doing. This allows us to capture the results of our tests in a structured way.
This means we can then use the structure output to then evaluate our code / application / agent.

### Logging Test Results
`results_bag` is a fixture that we can log values to from our tests. This is then captured by the `pytest-harvest` plugin.

```python
def test_my_agent(results_bag):
    results_bag.input = "my_value"
    results_bag.output = "my_output"
    results_bag.expected_output = "my_expected_output"
```

We can then access the results in the `results_bag` from the `pytest-harvest` plugin via the `module_results_df` fixture.

```python
def test_print_results(module_results_df):
    print(module_results_df.columns) # this will include "input", "output", "expected_output"
    print(module_results_df.head()) # this will show the first few rows of the results
    # TODO: Add more evaluation logic here or log the results to a file, etc.
```

### Parameterizing Tests
We can also parameterize tests to run the same test with different inputs.

```python
import pytest

@pytest.mark.parametrize(
    "input, expected_output",
    [
        ("input1", "output1"),
        ("input2", "output2"),
    ],
    ids=["test1", "test2"] # these are the test names for the above inputs
)
def test_my_agent(input, expected_output, results_bag):
    results_bag.input = input
    results_bag.expected_output = expected_output
    results_bag.output = my_agent(input) # your code here
    # can include static measures / evaluations here
    results_bag.success = results_bag.output == results_bag.expected_output
```

### Using Burr's Pytest Hook
With Burr you can curate test cases from real application runs. You can then use these test cases in your Pytest suite.
Burr has a hook that enables you to curate a file with the input state and expected output state for an entire run,
or a single action.  See the [Burr test case creation documentation](https://burr.dagworks.io/examples/guardrails/creating_tests/) for more
details on how. Here we show you how you can combine this with getting results:

```python
import pytest
from our_agent_application import prompt_for_more

from burr.core import state

# the following is required to run file based tests
from burr.testing import pytest_generate_tests  # noqa: F401

@pytest.mark.file_name("prompt_for_more.json") # our fixture file with the expected inputs and outputs
def test_an_agent_action(input_state, expected_state, results_bag):
    """Function for testing an individual action of our agent."""
    input_state = state.State.deserialize(input_state)
    expected_state = state.State.deserialize(expected_state)
    _, output_state = prompt_for_more(input_state)  # exercising an action of our agent

    results_bag.input_state = input_state
    results_bag.expected_state = expected_state
    results_bag.output_state = output_state
    results_bag.foo = "bar"
    # TODO: choose appropriate way to evaluate the output
    # e.g. exact match, fuzzy match, LLM grade, etc.
    # this is exact match here on all values in state
    exact_match = output_state == expected_state
    # for output that varies, you can do something like this
    # assert 'some value' in output_state["response"]["content"]
    # or, have an LLM Grade things -- you need to create the llm_evaluator function:
    # assert llm_evaluator("are these two equivalent responses. Respond with Y for yes, N for no",
    # output_state["response"]["content"], expected_state["response"]["content"]) == "Y"
    # store it in the results bag
    results_bag.correct = exact_match

    # place any asserts at the end of the test
    assert exact_match
```
So if we want to test an entire agent, we can use the same approach, but instead rely on the input and output
state being the entire state of the agent at the start and end of the run.

```python
import pytest
from our_agent_application import agent_builder, agent_runner # some functions that build and run our agent

from burr.core import state

# the following is required to run file based tests
from burr.testing import pytest_generate_tests  # noqa: F401

@pytest.mark.file_name("e2e.json") # our fixture file with the expected inputs and outputs
def test_an_agent_e2e(input_state, expected_state, results_bag):
    """Function for testing an agent end-to-end."""
    input_state = state.State.deserialize(input_state)
    expected_state = state.State.deserialize(expected_state)
    # exercise the agent
    agent = agent_builder(input_state)
    output_state = agent_runner(agent)

    results_bag.input_state = input_state
    results_bag.expected_state = expected_state
    results_bag.output_state = output_state
    results_bag.foo = "bar"
    # TODO: choose appropriate way to evaluate the output
    # e.g. exact match, fuzzy match, LLM grade, etc.
    # this is exact match here on all values in state
    exact_match = output_state == expected_state
    # for output that varies, you can do something like this
    # assert 'some value' in output_state["response"]["content"]
    # or, have an LLM Grade things -- you need to create the llm_evaluator function:
    # assert llm_evaluator("are these two equivalent responses. Respond with Y for yes, N for no",
    # output_state["response"]["content"], expected_state["response"]["content"]) == "Y"
    # store it in the results bag
    results_bag.correct = exact_match

    # place any asserts at the end of the test
    assert exact_match

```
