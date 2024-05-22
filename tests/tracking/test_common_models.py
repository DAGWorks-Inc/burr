from burr.core import Action, State
from burr.tracking.common.models import ActionModel


class ActionWithCustomSource(Action):
    def __init__(self):
        super().__init__()

    @property
    def reads(self) -> list[str]:
        return []

    def run(self, state: State, **run_kwargs) -> dict:
        return {}

    @property
    def writes(self) -> list[str]:
        return []

    def update(self, result: dict, state: State) -> State:
        return state

    def get_source(self) -> str:
        return "custom source code"


def test_action_with_custom_source():
    model = ActionModel.from_action(ActionWithCustomSource().with_name("foo"))
    assert model.code == "custom source code"
