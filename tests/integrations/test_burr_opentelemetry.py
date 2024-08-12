import json

import pydantic
import pytest

from burr.core import serde
from burr.integrations.opentelemetry import convert_to_otel_attribute


class TestModel(pydantic.BaseModel):
    foo: int
    bar: bool


@pytest.mark.parametrize(
    "value, expected",
    [
        ("hello", "hello"),
        (1, 1),
        ((1, 1), [1, 1]),
        ((1.0, 1.0), [1.0, 1.0]),
        ((True, True), [True, True]),
        (("hello", "hello"), ["hello", "hello"]),
        (TestModel(foo=1, bar=True), json.dumps(serde.serialize(TestModel(foo=1, bar=True)))),
    ],
)
def test_convert_to_otel_attribute(value, expected):
    assert convert_to_otel_attribute(value) == expected
