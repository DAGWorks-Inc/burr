from haystack import Pipeline, component
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore

from burr.core import State, action
from burr.core.graph import GraphBuilder
from burr.integrations.haystack import HaystackAction, haystack_pipeline_to_burr_graph


@component
class MockComponent:
    def __init__(self, required_init: str, optional_init: str = "default"):
        self.required_init = required_init
        self.optional_init = optional_init

    @component.output_types(output_1=str, output_2=str)
    def run(self, required_input: str, optional_input: str = "default") -> dict:
        return {
            "output_1": required_input,
            "output_2": optional_input,
        }


@action(reads=["query_embedding"], writes=["documents"])
def retrieve_documents(state: State) -> State:
    query_embedding = state["query_embedding"]

    document_store = InMemoryDocumentStore()
    retriever = InMemoryEmbeddingRetriever(document_store)

    results = retriever.run(query_embedding=query_embedding)
    return state.update(documents=results["documents"])


haystack_retrieve_documents = HaystackAction(
    component=InMemoryEmbeddingRetriever(InMemoryDocumentStore()),
    name="retrieve_documents",
    reads=["query_embedding"],
    writes=["documents"],
)


def test_input_socket_mapping():
    # {input_socket_name: state_field}
    reads = {"required_input": "foo"}

    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=reads, writes=[]
    )

    assert haction.reads == list(set(reads.values())) == ["foo"]


def test_input_socket_sequence():
    # {input_socket_name: input_socket_name}
    reads = ["required_input"]

    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=reads, writes=[]
    )

    assert haction.reads == list(reads) == ["required_input"]


def test_output_socket_mapping():
    # {state_field: output_socket_name}
    writes = {"bar": "output_1"}

    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=[], writes=writes
    )

    assert haction.writes == list(writes.keys()) == ["bar"]


def test_output_socket_sequence():
    # {output_socket_name: output_socket_name}
    writes = ["output_1"]

    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=[], writes=writes
    )

    assert haction.writes == writes == ["output_1"]


def test_get_component_source():
    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=[], writes=[]
    )

    expected_source = """\
@component
class MockComponent:
    def __init__(self, required_init: str, optional_init: str = "default"):
        self.required_init = required_init
        self.optional_init = optional_init

    @component.output_types(output_1=str, output_2=str)
    def run(self, required_input: str, optional_input: str = "default") -> dict:
        return {
            "output_1": required_input,
            "output_2": optional_input,
        }
"""

    assert haction.get_source() == expected_source


def test_run_with_external_inputs():
    state = State(initial_values={})
    haction = HaystackAction(
        component=MockComponent(required_init="init"), name="mock", reads=[], writes=[]
    )

    results = haction.run(state=state, required_input="as_input")

    assert results == {"output_1": "as_input", "output_2": "default"}


def test_run_with_state_inputs():
    state = State(initial_values={"foo": "bar"})
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads={"required_input": "foo"},
        writes=[],
    )

    results = haction.run(state=state)

    assert results == {"output_1": "bar", "output_2": "default"}


def test_run_with_bound_params():
    state = State(initial_values={})
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads=[],
        writes=[],
        bound_params={"required_input": "baz"},
    )

    results = haction.run(state=state)

    assert results == {"output_1": "baz", "output_2": "default"}


def test_run_mixed_params():
    state = State(initial_values={"foo": "bar"})
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads={"required_input": "foo"},
        writes=[],
        bound_params={"optional_input": "baz"},
    )

    results = haction.run(state=state)

    assert results == {"output_1": "bar", "output_2": "baz"}


def test_run_with_sequence():
    state = State(initial_values={"required_input": "bar"})
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads=["required_input"],
        writes=[],
    )

    results = haction.run(state=state)

    assert results == {"output_1": "bar", "output_2": "default"}


def test_update_with_writes_mapping():
    state = State(initial_values={})
    results = {"output_1": 1, "output_2": 2}
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads=[],
        writes={"foo": "output_1"},
    )

    new_state = haction.update(result=results, state=state)

    assert new_state["foo"] == 1


def test_update_with_writes_sequence():
    state = State(initial_values={})
    results = {"output_1": 1, "output_2": 2}
    haction = HaystackAction(
        component=MockComponent(required_init="init"),
        name="mock",
        reads=[],
        writes=["output_1"],
    )

    new_state = haction.update(result=results, state=state)

    assert new_state["output_1"] == 1


def test_pipeline_converter():
    # create haystack Pipeline
    retriever = InMemoryEmbeddingRetriever(InMemoryDocumentStore())
    text_embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")

    basic_rag_pipeline = Pipeline()
    basic_rag_pipeline.add_component("text_embedder", text_embedder)
    basic_rag_pipeline.add_component("retriever", retriever)
    basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

    # create Burr application
    embed_text = HaystackAction(
        component=text_embedder,
        name="text_embedder",
        reads=[],
        writes={"query_embedding": "embedding"},
    )

    retrieve_documents = HaystackAction(
        component=retriever,
        name="retriever",
        reads=["query_embedding"],
        writes=["documents"],
    )

    burr_graph = (
        GraphBuilder()
        .with_actions(embed_text, retrieve_documents)
        .with_transitions(("text_embedder", "retriever"))
        .build()
    )

    # convert the Haystack Pipeline to a Burr graph
    haystack_graph = haystack_pipeline_to_burr_graph(basic_rag_pipeline)

    converted_action_names = [action.name for action in haystack_graph.actions]
    for graph_action in burr_graph.actions:
        assert graph_action.name in converted_action_names

    for burr_t in burr_graph.transitions:
        assert any(
            burr_t.from_.name == haystack_t.from_.name and burr_t.to.name == haystack_t.to.name
            for haystack_t in haystack_graph.transitions
        )
