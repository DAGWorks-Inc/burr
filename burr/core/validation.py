from typing import Any, Optional

BASE_ERROR_MESSAGE = (
    "-------------------------------------------------------------------\n"
    "Oh no an error! Need help with Burr?\n"
    "Join our discord and ask for help! https://discord.gg/4FxBMyzW5n\n"
    "-------------------------------------------------------------------\n"
)


def assert_set(value: Optional[Any], field: str, method: str):
    if value is None:
        raise ValueError(
            BASE_ERROR_MESSAGE
            + f"Must call `{method}` before building application! Do so with ApplicationBuilder."
        )
