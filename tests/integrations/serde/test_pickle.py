from burr.core import serde, state
from burr.integrations.serde import pickle


class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email


def test_serde_of_pickle_object():
    pickle.register_type_to_pickle(User)
    user = User(name="John Doe", email="john.doe@example.com")
    og = state.State({"user": user, "test": "test"})
    serialized = og.serialize()
    assert serialized == {
        "user": {
            serde.KEY: "pickle",
            "value": b"\x80\x04\x95Q\x00\x00\x00\x00\x00\x00\x00\x8c\x0btest_pi"
            b"ckle\x94\x8c\x04User\x94\x93\x94)\x81\x94}\x94(\x8c\x04na"
            b"me\x94\x8c\x08John Doe\x94\x8c\x05email\x94\x8c\x14john"
            b".doe@example.com\x94ub.",
        },
        "test": "test",
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["user"], User)
    assert ng["user"].name == "John Doe"
    assert ng["user"].email == "john.doe@example.com"
