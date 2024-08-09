import os
from pathlib import Path

from tortoise import Tortoise, run_async

from burr.tracking.server.s3 import settings

DB_PATH = Path("~/.burr_server/db.sqlite3").expanduser()


async def connect():
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    await Tortoise.init(
        config=settings.TORTOISE_ORM,
    )


#
async def first_time_init():
    await connect()
    # Generate the schema
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    # db_path = sys.argv[1]
    run_async(first_time_init())
