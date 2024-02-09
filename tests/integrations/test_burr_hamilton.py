import pytest

from burr.core import State
from burr.integrations.hamilton import Hamilton, from_state, from_value, update_state
from hamilton import ad_hoc_utils, driver


def _incrementing_driver():
    def incremented_count(current_count: int) -> int:
        return current_count + 1

    def incremented_count_2(current_count: int, increment_by: int = 1) -> int:
        return current_count + increment_by

    def sum_of_counts(incremented_count: int, incremented_count_2: int) -> int:
        return incremented_count + incremented_count_2

    mod = ad_hoc_utils.create_temporary_module(
        incremented_count, incremented_count_2, sum_of_counts
    )
    dr = driver.Driver({}, mod)
    return dr


def test_set_driver():
    dr = _incrementing_driver()
    Hamilton.set_driver(dr)
    h = Hamilton({}, {}, driver=dr)
    assert h.driver == dr


def test__extract_inputs_overrides():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count": from_state("count"), "incremented_count_2": from_value(2)},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    inputs, overrides = h._extract_inputs_overrides(State({"count": 0}))
    assert inputs == {"current_count": 0}
    assert overrides == {"incremented_count_2": 2}


def test__extract_inputs_overrides_missing_inputs():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count_not_present": from_state("count")},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    with pytest.raises(ValueError, match="not available"):
        inputs, _ = h._extract_inputs_overrides(State({"count": 0}))


def test_reads():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count": from_state("count"), "incremented_count_2": from_value(2)},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    assert h.reads == ["count"]


def test_writes():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count": from_state("count"), "incremented_count_2": from_value(2)},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    assert h.writes == ["count"]


def test_run_step_with_multiple_inputs():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count": from_state("count"), "increment_by": from_value(5)},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    result = h.run(State({"count": 1}))
    assert result == {"sum_of_counts": 8}
    new_state = h.update(result, State({"count": 1}))
    assert new_state.get_all() == {"count": 8}


def test_run_step_with_overrides():
    dr = _incrementing_driver()
    h = Hamilton(
        inputs={"current_count": from_state("count"), "incremented_count_2": from_value(2)},
        outputs={"sum_of_counts": update_state("count")},
        driver=dr,
    )
    result = h.run(State({"count": 1}))
    assert result == {"sum_of_counts": 4}
    new_state = h.update(result, State({"count": 1}))
    assert new_state.get_all() == {"count": 4}
