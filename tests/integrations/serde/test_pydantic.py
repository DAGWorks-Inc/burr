from pydantic import BaseModel

from burr.core import serde, state


class User(BaseModel):
    name: str
    email: str


def test_serde_of_pydantic_model():
    user = User(name="John Doe", email="john.doe@example.com")
    og = state.State({"user": user})
    serialized = og.serialize()
    assert serialized == {
        "user": {
            serde.KEY: "pydantic",
            "__pydantic_class": "test_pydantic.User",
            "email": "john.doe@example.com",
            "name": "John Doe",
        }
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["user"], User)
    assert ng["user"].name == "John Doe"
    assert ng["user"].email == "john.doe@example.com"
