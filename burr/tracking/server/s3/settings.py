from pathlib import Path

DB_PATH = Path("~/.burr_server/db.sqlite3").expanduser()

TORTOISE_ORM = {
    "connections": {"default": f"sqlite:///{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["burr.tracking.server.s3.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
