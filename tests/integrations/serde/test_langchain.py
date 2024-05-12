from langchain_community.document_transformers.embeddings_redundant_filter import _DocumentWithState
from langchain_core import documents as lc_documents
from langchain_core import messages as lc_messages

from burr.core import serde, state


def test_serde_of_lc_document():
    doc = lc_documents.Document(page_content="test content")
    og = state.State({"doc": doc})
    serialized = og.serialize()
    assert serialized == {
        "doc": {
            serde.KEY: "lc_document",
            "id": ["langchain", "schema", "document", "Document"],
            "kwargs": {"page_content": "test content", "type": "Document"},
            "lc": 1,
            "type": "constructor",
        }
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["doc"], lc_documents.Document)
    assert ng["doc"].page_content == "test content"
    assert serde.KEY not in ng


def test_serde_of_lc_message():
    message = lc_messages.HumanMessage(content="test content")
    og = state.State({"message": message})
    serialized = og.serialize()
    assert serialized == {
        "message": {
            serde.KEY: "lc_message",
            "data": {
                "additional_kwargs": {},
                "content": "test content",
                "example": False,
                "id": None,
                "name": None,
                "response_metadata": {},
                "type": "human",
            },
            "type": "human",
        }
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["message"], lc_messages.HumanMessage)
    assert ng["message"].content == "test content"
    assert serde.KEY not in ng


def test_serde_of_document_with_state():
    """Tests that we can serialize a document that is not serializable to a document."""
    doc = _DocumentWithState(page_content="Hello, World document with state!", state={"foo": "bar"})
    og = state.State({"doc": doc})
    serialized = og.serialize()
    assert serialized == {
        "doc": {
            serde.KEY: "lc_document_with_state",
            "doc": {
                serde.KEY: "lc_document",
                "id": ["langchain", "schema", "document", "Document"],
                "kwargs": {"page_content": "Hello, World document with state!", "type": "Document"},
                "lc": 1,
                "type": "constructor",
            },
            "state": {"foo": "bar"},
        }
    }
    ng = state.State.deserialize(serialized)
    assert isinstance(ng["doc"], lc_documents.Document)
    assert ng["doc"].page_content == "Hello, World document with state!"
    assert serde.KEY not in ng
