import pathlib

import pytest

from burr.core.graph import GraphBuilder

from tests.core.test_graph import PassedInAction


@pytest.fixture
def base_counter_action():
    yield PassedInAction(
        reads=["count"],
        writes=["count"],
        fn=lambda state: {"count": state.get("count", 0) + 1},
        update_fn=lambda result, state: state.update(**result),
        inputs=[],
    )


@pytest.fixture
def graph(base_counter_action):
    yield (
        GraphBuilder()
        .with_actions(counter=base_counter_action)
        .with_transitions(("counter", "counter"))
        .build()
    )


@pytest.mark.parametrize(
    "filename, write_dot", [("app", False), ("app.png", False), ("app", True), ("app.png", True)]
)
def test_visualize_dot_output(graph, tmp_path: pathlib.Path, filename: str, write_dot: bool):
    """Handle file generation with `graph.Digraph` `.render()` and `.pipe()`"""
    output_file_path = f"{tmp_path}/{filename}"

    graph.visualize(
        output_file_path=output_file_path,
        write_dot=write_dot,
    )

    # assert pathlib.Path(tmp_path, "app.png").exists()
    assert pathlib.Path(tmp_path, "app").exists() == write_dot


def test_visualize_no_dot_output(graph, tmp_path: pathlib.Path):
    """Check that no dot file is generated when output_file_path=None"""
    dot_file_path = tmp_path / "dag"

    graph.visualize(output_file_path=None)

    assert not dot_file_path.exists()
