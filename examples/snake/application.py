import enum
import random
from time import sleep
from typing import Any, Dict, Optional, Tuple

import keyboard

from burr.core import Action, ApplicationBuilder, State, action, default, when
from burr.lifecycle import PostRunStepHook, PreRunStepHook

LATEST_KEYPRESS = None


class SnakeDirection(enum.Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    def get_vector(self):
        if self == SnakeDirection.UP:
            return 0, -1
        elif self == SnakeDirection.DOWN:
            return 0, 1
        elif self == SnakeDirection.LEFT:
            return -1, 0
        elif self == SnakeDirection.RIGHT:
            return 1, 0


class GamePauseHook(PreRunStepHook):
    def __init__(self, speed: float):
        self.speed = speed

    def pre_run_step(
        self, *, state: "State", action: "Action", inputs: Dict[str, Any], **future_kwargs: Any
    ):
        if action.name == "select_direction":
            sleep(self.speed)


def get_boundary_char(x, y, board_size: Tuple[int, int]):
    if x == -1 and y == -1:
        return "╔"
    elif x == -1 and y == board_size[1]:
        return "╚"
    elif x == board_size[0] and y == -1:
        return "╗"
    elif x == board_size[0] and y == board_size[1]:
        return "╝"
    elif x == -1 or x == board_size[0]:
        return "║"
    elif y == -1 or y == board_size[1]:
        return "═"
    return None


def display_board(snake_tiles, target_coors, board_size):
    for y in range(-1, board_size[1] + 1):
        for x in range(-1, board_size[0] + 1):
            boundary_char = get_boundary_char(x, y, board_size)
            if boundary_char:
                print(boundary_char, end="")
                continue
            if (x, y) in snake_tiles:
                print("□", end="")
            elif (x, y) == target_coors:
                print("◆", end="")
            else:
                print(" ", end="")
        print()


class GameRenderHook(PostRunStepHook):
    def post_run_step(
        self,
        *,
        state: "State",
        action: "Action",
        result: Optional[Dict[str, Any]],
        exception: Exception,
        **future_kwargs: Any,
    ):
        if action.name == "select_direction":
            display_board(state["snake_tiles"], state["target_coors"], state["board_size"])


def _push_latest_keypress(key):
    if key.name in [
        SnakeDirection.UP.value,
        SnakeDirection.DOWN.value,
        SnakeDirection.LEFT.value,
        SnakeDirection.RIGHT.value,
    ]:
        global LATEST_KEYPRESS
        LATEST_KEYPRESS = key


def _pop_latest_keypress() -> Optional[str]:
    global LATEST_KEYPRESS
    latest = LATEST_KEYPRESS
    LATEST_KEYPRESS = None
    return latest


keyboard.on_press(_push_latest_keypress)


@action(reads=[], writes=["snake_tiles", "target_coors", "board_size"])
def start(
    state: State,
    start_coors: Tuple[int, int],
    target_coors: Tuple[int, int],
    board_size: Tuple[int, int],
):
    # TODO -- validate start and target coors
    result = {
        "snake_tiles": [start_coors],
        "target_coors": target_coors,
        "board_size": board_size,
    }
    return result, state.update(**result)


@action(reads=["snake_direction"], writes=["snake_direction"])
def select_direction(state: State):
    latest_keypress = (
        _pop_latest_keypress()
    )  # TODO -- make this an input (or a callback which we don't have yet...)
    if latest_keypress is not None:
        result = {"snake_direction": SnakeDirection(latest_keypress.name)}
    else:
        result = {
            "snake_direction": state["snake_direction"],
        }
    return result, state.update(**result)


@action(reads=["snake_tiles", "snake_direction"], writes=["snake_tiles"])
def move_snake(state: State):
    direction = state["snake_direction"]
    snake_tiles = state["snake_tiles"]
    head = snake_tiles[0]
    dx, dy = direction.get_vector()
    new_head = (head[0] + dx, head[1] + dy)
    snake_tiles = [new_head] + snake_tiles[:-1]
    result = {
        "snake_tiles": snake_tiles,
    }
    return result, state.update(**result)


@action(reads=["snake_tiles"], writes=["collision"])
def check_collision(state: State):
    snake_tiles = state["snake_tiles"]
    head = snake_tiles[0]
    result = {
        "collision": head in snake_tiles[1:],
    }
    return result, state.update(**result)


@action(reads=["snake_tiles", "board_size"], writes=["edge_collision"])
def check_edge_collision(state: State):
    snake_tiles = state["snake_tiles"]
    head = snake_tiles[0]
    board_size = state["board_size"]
    result = {
        "edge_collision": head[0] < 0
        or head[0] >= board_size[0]
        or head[1] < 0
        or head[1] >= board_size[1],
    }
    return result, state.update(**result)


def _get_target_coors(board_size, snake_tiles):
    while True:
        test_coors = (random.randint(0, board_size[0]), random.randint(0, board_size[1]))
        if test_coors not in snake_tiles:
            return test_coors


@action(reads=["snake_tiles", "target_coors", "board_size"], writes=["target_coors", "snake_tiles"])
def check_target(state: State):
    snake_tiles = state["snake_tiles"]
    target_coors = state["target_coors"]
    head = snake_tiles[0]
    board_size = state["board_size"]
    if head == target_coors:
        snake_tiles = [target_coors] + snake_tiles
        result = {
            "snake_tiles": snake_tiles,
            "target_coors": _get_target_coors(board_size, snake_tiles),
        }
    else:
        result = {
            "snake_tiles": snake_tiles,
        }
    return result, state.update(**result)


@action(reads=[], writes=["game_over"])
def game_over(state: State):
    result = {"game_over": True}
    return result, state.update(**result)


class DebuggerAction(Action):
    def __init__(self, *fields):
        super(DebuggerAction, self).__init__()
        self.fields = fields

    @property
    def reads(self) -> list[str]:
        return self.fields

    def run(self, state: State, **run_kwargs) -> dict:
        import pdb

        pdb.set_trace()

    @property
    def writes(self) -> list[str]:
        return []

    def update(self, result: dict, state: State) -> State:
        return state


def application():
    return (
        ApplicationBuilder()
        .with_actions(
            start=start,
            select_direction=select_direction,
            move_snake=move_snake,
            check_collision=check_collision,
            check_edge_collision=check_edge_collision,
            check_target=check_target,
            game_over=game_over,
            debug=DebuggerAction("snake_tiles", "snake_direction", "target_coors", "board_size"),
        )
        .with_entrypoint("start")
        .with_state(snake_tiles=[], snake_direction=SnakeDirection.UP)
        .with_transitions(
            ("start", "select_direction", default),
            ("select_direction", "move_snake"),
            ("move_snake", "check_collision"),
            ("check_collision", "game_over", when(collision=True)),
            ("check_collision", "check_edge_collision", default),
            ("check_edge_collision", "game_over", when(edge_collision=True)),
            ("check_edge_collision", "check_target", default),
            ("check_target", "select_direction", default),
        )
        .with_tracker(project="demo:snake")
        .with_hooks(GamePauseHook(speed=1), GameRenderHook())
        .with_global_params(__callback=...)
        .build()
    )


def play():
    start_coors = (5, 5)
    target_coors = (7, 7)
    board_size = (10, 10)
    app = application()
    for action_, result, state_ in app.iterate(
        inputs={"start_coors": start_coors, "target_coors": target_coors, "board_size": board_size},
        halt_after=["game_over"],
    ):
        pass


if __name__ == "__main__":
    app = application()
    app.visualize("./out", format="png", view=False, include_state=True, include_conditions=True)
    play()
    # curses.wrapper(play)
