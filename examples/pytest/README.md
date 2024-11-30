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
