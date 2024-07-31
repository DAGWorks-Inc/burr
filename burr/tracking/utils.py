import json


def safe_json_load(line: bytes):
    # Every once in a while we'll hit a non-utf-8 character
    # In this case we replace it and hope for the best
    return json.loads(line.decode("utf-8", errors="replace"))
