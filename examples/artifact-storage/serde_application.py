# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Demonstrates externalizing large values through Burr's serde layer instead of from actions.

Here the actions keep the *live* value (a ``Document``) in state. A type-based serializer --
which receives the application's object store through ``serialization_context`` -- writes the
document's bytes to the store whenever state is persisted, so the persisted state only holds a
small ``ArtifactRef``. Resuming the application loads that reference lazily (no download).
"""

import os
import tempfile
from typing import Optional

from burr.core import Application, ApplicationBuilder, Result, State, action, serde
from burr.core.artifacts import ArtifactRef, LocalFileSystemArtifactStore
from burr.core.persistence import SQLitePersister
from burr.core.serde import SerializationContext


class Document:
    """Stands in for any large value you'd rather not embed in persisted state."""

    def __init__(self, content: bytes):
        self.content = content


@serde.serialize.register(Document)
def serialize_document(
    value: Document, serialization_context: SerializationContext = None, **kwargs
) -> dict:
    store = serialization_context.require_object_store()
    ref = store.put_artifact(value.content, media_type="text/plain")
    return {serde.KEY: "example_document", "ref": serde.serialize(ref)}


@serde.deserializer.register("example_document")
def deserialize_document(value: dict, **kwargs) -> ArtifactRef:
    # Lazy: hand back the reference rather than downloading the content on every load.
    return serde.deserialize(value["ref"])


@action(reads=[], writes=["document"])
def receive_document(state: State, content: bytes) -> State:
    return state.update(document=Document(content))


@action(reads=["document"], writes=["word_count"])
def count_words(state: State) -> State:
    return state.update(word_count=len(state["document"].content.split()))


def application(
    storage_dir: str, app_id: str = "serde-example", resume: bool = False
) -> Application:
    """Builds the application, persisting state to SQLite and artifacts to ``storage_dir``.

    :param storage_dir: Directory holding both the SQLite database and the artifact store.
    :param app_id: Application ID to persist under / resume.
    :param resume: Whether to resume ``app_id`` from its persisted state.
    """
    persister = SQLitePersister.from_values(db_path=os.path.join(storage_dir, "state.db"))
    persister.initialize()
    builder = (
        ApplicationBuilder()
        .with_actions(receive_document, count_words, result=Result("word_count"))
        .with_transitions(("receive_document", "count_words"), ("count_words", "result"))
        .with_identifiers(app_id=app_id)
        .with_state_persister(persister)
        .with_object_store(LocalFileSystemArtifactStore(os.path.join(storage_dir, "artifacts")))
    )
    if resume:
        builder = builder.initialize_from(
            persister,
            resume_at_next_action=True,
            default_state={},
            default_entrypoint="receive_document",
        )
    else:
        builder = builder.with_entrypoint("receive_document")
    return builder.build()


def main(storage_dir: Optional[str] = None) -> None:
    storage_dir = storage_dir or tempfile.mkdtemp()
    content = b"A document far too large to keep embedded in persisted state. " * 1000

    app = application(storage_dir)
    *_, state = app.run(halt_after=["result"], inputs={"content": content})
    print(f"Word count: {state['word_count']}")

    resumed = application(storage_dir, resume=True)
    ref = resumed.state["document"]
    print(f"Resumed with a {type(ref).__name__} for {ref.size_bytes} bytes (nothing downloaded)")
    store = LocalFileSystemArtifactStore(os.path.join(storage_dir, "artifacts"))
    assert ref.read(store) == content


if __name__ == "__main__":
    main()
