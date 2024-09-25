from __future__ import annotations

import os

"""This tests that the pydantic integration allows for future import of annotations"""

file_name = os.path.join(os.path.dirname(__file__), "test_burr_pydantic.py")
eval(compile(open(file_name).read(), file_name, "exec"))
