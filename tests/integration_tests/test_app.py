import pydantic
from langchain_core import documents

from burr import core
from burr.core import State, action, expr, persistence, state
from burr.tracking import client as tracking_client


@action(reads=[], writes=["dict"])
def basic_action(state: State, user_input: str) -> tuple[dict, State]:
    v = {"foo": 1, "bar": "2", "bool": True, "None": None, "input": user_input}
    return {"dict": v}, state.update(dict=v)


class PydanticField(pydantic.BaseModel):
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


def build_application(sqllite_persister, tracker, partition_key, app_id):
    persister = sqllite_persister or tracker
    app_builder = (
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
            persister,
            resume_at_next_action=True,
            default_state={
                "custom_field": documents.Document(
                    page_content="this is a custom field to serialize"
                )
            },
            default_entrypoint="basic_action",
        )
    )
    if sqllite_persister:
        app_builder.with_state_persister(sqllite_persister)
    if tracker:
        app_builder.with_tracker(tracker)
    return app_builder.build()


def register_custom_serde_for_lc_document(field_name: str):
    """Register a custom serde for a field"""

    def my_field_serializer(value: documents.Document, **kwargs) -> dict:
        serde_value = f"serialized::{value.page_content}"
        return {"value": serde_value}

    def my_field_deserializer(value: dict, **kwargs) -> documents.Document:
        serde_value = value["value"]
        return documents.Document(page_content=serde_value.replace("serialized::", ""))

    state.register_field_serde(field_name, my_field_serializer, my_field_deserializer)


def test_whole_application_tracker(tmp_path):
    """This test creates an application and then steps through it rebuilding the
    application each time. This is a test of things being serialized and deserialized."""
    tracker = tracking_client.LocalTrackingClient("integration-test", tmp_path)
    app_id = "integration-test"
    partition_key = ""
    # step 1
    app = build_application(None, tracker, partition_key, app_id)
    register_custom_serde_for_lc_document("custom_field")
    action1, result1, state1 = app.step(inputs={"user_input": "hello"})
    # check custom serde
    assert state1.serialize() == {
        "__PRIOR_STEP": "basic_action",
        "__SEQUENCE_ID": 0,
        "custom_field": {"value": "serialized::this is a custom field to serialize"},
        "dict": {"None": None, "bar": "2", "bool": True, "foo": 1, "input": "hello"},
    }
    assert action1.name == "basic_action"
    # step 2
    app = build_application(None, tracker, partition_key, app_id)
    action2, result2, state2 = app.step()
    assert action2.name == "pydantic_action"
    # step 3
    app = build_application(None, tracker, partition_key, app_id)
    action3, result3, state3 = app.step()
    assert action3.name == "langchain_action"
    # step 4
    app = build_application(None, tracker, partition_key, app_id)
    action4, result4, state4 = app.step()
    assert action4.name == "terminal_action"

    # assert that state is basically the same across different steps
    assert state1["dict"] == {"foo": 1, "bar": "2", "bool": True, "None": None, "input": "hello"}
    assert state1["dict"] == state4["dict"]

    assert state2["pydantic_field"].f1 == 1
    assert state2["pydantic_field"].f2 is True
    assert state2["pydantic_field"] == state3["pydantic_field"]

    assert state3["lc_doc"].page_content == "foo: 1, bar: True"
    assert state3["lc_doc"] == state4["lc_doc"]

    # assert that tracker has things in it too
    final_tracker_state = tracker.load(partition_key, app_id=app_id)
    for k, v in final_tracker_state["state"].items():
        assert v == state4[k]


def test_whole_application_sqllite(tmp_path):
    """This test creates an application and then steps through it rebuilding the
    application each time. This is a test of things being serialized and deserialized."""
    sqllite_persister = persistence.SQLLitePersister(tmp_path / "test.db")
    sqllite_persister.initialize()
    app_id = "integration-test"
    partition_key = ""
    # step 1
    app = build_application(sqllite_persister, None, partition_key, app_id)
    register_custom_serde_for_lc_document("custom_field")
    action1, result1, state1 = app.step(inputs={"user_input": "hello"})
    # check custom serde
    assert state1.serialize() == {
        "__PRIOR_STEP": "basic_action",
        "__SEQUENCE_ID": 0,
        "custom_field": {"value": "serialized::this is a custom field to serialize"},
        "dict": {"None": None, "bar": "2", "bool": True, "foo": 1, "input": "hello"},
    }
    # check actions
    assert action1.name == "basic_action"
    # step 2
    app = build_application(sqllite_persister, None, partition_key, app_id)
    action2, result2, state2 = app.step()
    assert action2.name == "pydantic_action"
    # step 3
    app = build_application(sqllite_persister, None, partition_key, app_id)
    action3, result3, state3 = app.step()
    assert action3.name == "langchain_action"
    # step 4
    app = build_application(sqllite_persister, None, partition_key, app_id)
    action4, result4, state4 = app.step()
    assert action4.name == "terminal_action"

    # assert that state is basically the same across different steps
    assert state1["dict"] == {"foo": 1, "bar": "2", "bool": True, "None": None, "input": "hello"}
    assert state1["dict"] == state4["dict"]

    assert state2["pydantic_field"].f1 == 1
    assert state2["pydantic_field"].f2 is True
    assert state2["pydantic_field"] == state3["pydantic_field"]

    assert state3["lc_doc"].page_content == "foo: 1, bar: True"
    assert state3["lc_doc"] == state4["lc_doc"]

    final_sqllite_state = sqllite_persister.load("", app_id=app_id)
    assert final_sqllite_state["state"] == state4
    assert sqllite_persister.list_app_ids(partition_key="") == ["integration-test"]
