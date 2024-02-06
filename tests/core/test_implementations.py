import pytest

from burr.core import State
from burr.core.implementations import Placeholder


def test_placedholder_action():
    action = Placeholder(reads=["foo"], writes=["bar"]).with_name("test")
    assert action.reads == ["foo"]
    assert action.writes == ["bar"]
    with pytest.raises(NotImplementedError):
        action.run(State({}))

    with pytest.raises(NotImplementedError):
        action.update({}, State({}))
