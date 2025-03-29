import os

BURR_SERVER_ROOT = os.environ.get("BURR_SERVER_ROOT", os.path.expanduser("~/.burr_server"))
BURR_DB_FILENAME = os.environ.get("BURR_DB_FILENAME", "db.sqlite3")

DB_PATH = os.path.join(
    BURR_SERVER_ROOT,
    BURR_DB_FILENAME,
)
TORTOISE_ORM = {
    "connections": {"default": f"sqlite:///{DB_PATH}"},
    "apps": {
        "models": {
            "models": ["burr.tracking.server.s3.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
