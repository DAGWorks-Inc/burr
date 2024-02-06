from burr.core import State
from burr.core.action import Action


class Placeholder(Action):
    """This is a placeholder action -- you would expect it to break if you tried to run it. It is specifically
    for the following workflow:
    1. Create your state machine out of placeholders to model it
    2. Visualize the state machine
    2. Replace the placeholders with real actions as you see fit
    """

    def __init__(self, reads: list[str], writes: list[str]):
        super().__init__()
        self._reads = reads
        self._writes = writes

    def run(self, state: State) -> dict:
        raise NotImplementedError(
            f"This is a placeholder action and thus you are unable to run. Please implement: {self}!"
        )

    def update(self, result: dict, state: State) -> State:
        raise NotImplementedError(
            f"This is a placeholder action and thus cannot update state. Please implement: {self}!"
        )

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes
