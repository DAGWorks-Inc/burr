import datetime
import os
import sys

IS_WINDOWS = os.name == "nt"

if sys.version_info >= (3, 11):
    utc = datetime.UTC
else:
    utc = datetime.timezone.utc


def now():
    return datetime.datetime.now(utc)
