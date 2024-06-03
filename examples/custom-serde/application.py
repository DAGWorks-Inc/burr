import pydantic
from langchain_core import documents

from burr import core
from burr.core import State, action, expr, serde, state
from burr.tracking import client as tracking_client


# say we have have a custom class that we want to serialize
# and deserialize using custom serde
class CustomClass(object):
    """Custom class we'll use to test custom serde"""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        # required for asserts etc to work
        return self.value == other.value


# create custom serializer for the custom class & register it
@serde.serialize.register(CustomClass)
def serialize_customclass(value: CustomClass, **kwargs) -> dict:
    """Serializes the custom class however we want

    :param value: the value to serialize.
    :param kwargs:
    :return: dictionary of serde.KEY and value
    """
    return {
        serde.KEY: "CustomClass",  # this has to map to the value regisered for the deserializer below
        "value": f"[value=={value.value}]",  # serialize the value however we want
    }


# create custom deserializer for the custom class & register it
@serde.deserializer.register("CustomClass")
def deserialize_customclass(value: dict, **kwargs) -> CustomClass:
    """Deserializes the value using whatever meands we want

    :param value: the value to deserialize from.
    :param kwargs:
    :return: CustomClass
    """
    # deserialize the value however we want
    return CustomClass(value=value["value"].split("==")[1][0:-1])


# register custom serde for the custom field
def my_field_serializer(value: documents.Document, **kwargs) -> dict:
    serde_value = f"serialized::{value.page_content}"
    return {"value": serde_value}


def my_field_deserializer(value: dict, **kwargs) -> documents.Document:
    serde_value = value["value"]
    return documents.Document(page_content=serde_value.replace("serialized::", ""))


state.register_field_serde("custom_field", my_field_serializer, my_field_deserializer)

# --- define the actions


@action(reads=[], writes=["dict"])
def basic_action(state: State, user_input: str) -> tuple[dict, State]:
    v = {
        "foo": 1,
        "bar": CustomClass("example value"),
        "bool": True,
        "None": None,
        "input": user_input,
    }
    return {"dict": v}, state.update(dict=v)


class PydanticField(pydantic.BaseModel):
    """burr handles serializing custom pydantic fields"""

    f1: int = 0
    f2: bool = False


@action(reads=["dict"], writes=["pydantic_field"])
def pydantic_action(state: State) -> tuple[dict, State]:
    v = PydanticField(f1=state["dict"]["foo"], f2=state["dict"]["bool"])
    return {"pydantic_field": v}, state.update(pydantic_field=v)


@action(reads=["pydantic_field"], writes=["lc_doc"])
def langchain_action(state: State) -> tuple[dict, State]:
    v = documents.Document(
        page_content=f"foo: {state['pydantic_field'].f1}, bar: {state['pydantic_field'].f2}"
    )
    return {"lc_doc": v}, state.update(lc_doc=v)


@action(reads=["lc_doc"], writes=[])
def terminal_action(state: State) -> tuple[dict, State]:
    return {"output": state["lc_doc"].page_content}, state


# build the application
def build_application(partition_key, app_id):
    """Builds the application"""
    tracker = tracking_client.LocalTrackingClient("serde-example")
    app = (
        core.ApplicationBuilder()
        .with_actions(basic_action, pydantic_action, langchain_action, terminal_action)
        .with_transitions(
            ("basic_action", "terminal_action", expr("dict['foo'] == 0")),
            ("basic_action", "pydantic_action"),
            ("pydantic_action", "langchain_action"),
            ("langchain_action", "terminal_action"),
        )
        .with_identifiers(partition_key=partition_key, app_id=app_id)
        .initialize_from(
            tracker,
            resume_at_next_action=True,
            default_state={
                "custom_field": documents.Document(
                    page_content="this is a custom field to serialize"
                )
            },
            default_entrypoint="basic_action",
        )
        .with_tracker(tracker)
        .build()
    )
    return app


if __name__ == "__main__":
    import pprint
    import uuid

    # build
    app = build_application("client-123", str(uuid.uuid4()))
    app.visualize(
        output_file_path="statemachine", include_conditions=True, include_state=True, format="png"
    )
    # run
    action, result, state = app.run(
        halt_after=["terminal_action"], inputs={"user_input": "hello world"}
    )
    # serialize
    serialized_state = state.serialize()
    pprint.pprint(serialized_state)
    # deserialize
    deserialized_state = State.deserialize(serialized_state)
    # assert that the state is the same after serialization and deserialization
    assert state.get_all() == deserialized_state.get_all()
