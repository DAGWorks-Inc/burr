import base64
import getpass
import hashlib
import os


def set_environment_variables():
    import dlt.destinations.impl.lancedb.models  # noqa

    if os.environ.get("OPENAI_API_KEY") is None:
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter OPENAI_API_KEY: ")

    os.environ["DESTINATION__LANCEDB__EMBEDDING_MODEL_PROVIDER"] = "openai"
    os.environ["DESTINATION__LANCEDB__EMBEDDING_MODEL"] = "text-embedding-3-small"

    os.environ["DESTINATION__LANCEDB__CREDENTIALS__URI"] = ".lancedb"
    os.environ["DESTINATION__LANCEDB__CREDENTIALS__EMBEDDING_MODEL_PROVIDER_API_KEY"] = os.environ[
        "OPENAI_API_KEY"
    ]


def instrument():
    from opentelemetry.instrumentation.lancedb import LanceInstrumentor
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    LanceInstrumentor().instrument()
    OpenAIInstrumentor().instrument()


def _compact_hash(digest: bytes) -> str:
    """Compact the hash to a string that's safe to pass around."""
    return base64.urlsafe_b64encode(digest).decode()


def hash_primitive(obj, *args, **kwargs) -> str:
    """Convert the primitive to a string and hash it"""
    hash_object = hashlib.md5(str(obj).encode())
    return _compact_hash(hash_object.digest())


def hash_set(obj, *args, **kwargs) -> str:
    """Hash each element of the set, then sort hashes, and
    create a hash of hashes.
    For the same objects in the set, the hashes will be the
    same.
    """
    hashes = (hash_primitive(elem) for elem in obj)
    sorted_hashes = sorted(hashes)

    hash_object = hashlib.sha224()
    for hash in sorted_hashes:
        hash_object.update(hash.encode())

    return _compact_hash(hash_object.digest())
