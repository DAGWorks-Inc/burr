# try to import to serialize Langchain messages
from langchain_core import documents as lc_documents
from langchain_core import load as lc_serde
from langchain_core import messages as lc_messages

from burr.core import serde


@serde.serialize.register(lc_documents.Document)
def serialize_lc_docs(value: lc_documents.Document, **kwargs) -> dict:
    """Serializes langchain documents."""
    if value.is_lc_serializable():
        lc_doc = lc_serde.dumpd(value)
        lc_doc[serde.KEY] = "lc_document"
        return lc_doc
    elif hasattr(value, "to_document") and hasattr(value, "state"):
        # attempt to serialize the state as well
        return {
            "doc": serialize_lc_docs(value.to_document()),
            "state": serde.serialize(value.state, **kwargs),
            serde.KEY: "lc_document_with_state",
        }
    elif hasattr(value, "to_document"):
        # we lose some state here, but it's better than nothing
        return serialize_lc_docs(value.to_document())
    else:
        # d.page_content  # hack because not all documents are serializable
        return {"value": value.page_content, serde.KEY: "lc_document_hack"}


@serde.deserializer.register("lc_document")
def deserialize_lc_document(value: dict, **kwargs) -> lc_documents.Document:
    """Deserializes langchain documents."""
    value.pop(serde.KEY)
    return lc_serde.load(value)


@serde.deserializer.register("lc_document_with_state")
def deserialize_lc_document_with_state(value: dict, **kwargs) -> lc_documents.Document:
    """Deserializes langchain documents with state."""
    from langchain_community.document_transformers.embeddings_redundant_filter import (
        _DocumentWithState,
    )

    value.pop(serde.KEY)
    doc = lc_serde.load(value["doc"])
    state = serde.deserialize(value["state"], **kwargs)
    return _DocumentWithState(page_content=doc.page_content, metadata=doc.metadata, state=state)


@serde.deserializer.register("lc_document_hack")
def deserialize_lc_document_hack(value: dict, **kwargs) -> lc_documents.Document:
    """Deserializes langchain documents that we didn't know about into a document."""
    return lc_documents.Document(page_content=value["value"])


@serde.serialize.register(lc_messages.BaseMessage)
def serialize_lc_messages(value: lc_messages.BaseMessage, **kwargs) -> dict:
    """Serializes langchain messages."""
    if value.is_lc_serializable():
        lc_message = lc_messages.message_to_dict(value)
        lc_message[serde.KEY] = "lc_message"
        return lc_message
    else:
        return {"value": value.content, "type": value.type, serde.KEY: "lc_message_hack"}


@serde.deserializer.register("lc_message")
def deserialize_lc_message(value: dict, **kwargs) -> lc_messages.BaseMessage:
    """Deserializes langchain messages."""
    value.pop(serde.KEY)  # note this mutates the dict
    return lc_messages._message_from_dict(value)


@serde.deserializer.register("lc_message_hack")
def deserialize_lc_message_hack(value: dict, **kwargs) -> lc_messages.BaseMessage:
    """Deserializes langchain messages that we didn't know how to serialize."""
    return lc_messages.BaseMessage(content=value["value"], type=value["type"])
