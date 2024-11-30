import pytest


# examples/pytest/test_example.py
def test_example(result_collector):
    result_collector.append("Test result 1")
    result_collector.append("Test result 2")
    assert True


@pytest.mark.parametrize("sample_idx", range(3))
def test_1(sample_idx, results_bag):
    results_bag.input = "..."
    results_bag.actual = "foo bar"
    results_bag.expected = "foo bar baz"
    results_bag.cosine = 0.8
    results_bag.jaccard = 0.6
    results_bag.llm = sample_idx


def test_2(results_bag):
    results_bag.input = "..."
    results_bag.actual = "foo"
    results_bag.expected = "foo bar baz"
    results_bag.cosine = 0.3
    results_bag.jaccard = 0.2
    print("hi")
    assert False


def test_print_results(module_results_df):
    print(module_results_df.columns)
    print(module_results_df.head())
    # save to CSV
    # upload to google sheets
    # compute statistics
