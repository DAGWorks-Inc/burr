import inspect
from collections.abc import Mapping
from typing import Any, Optional, Sequence, Union

from haystack import Pipeline
from haystack.core.component import Component
from haystack.core.component.types import _empty as haystack_empty

from burr.core.action import Action
from burr.core.graph import Graph, GraphBuilder
from burr.core.state import State


# TODO show OpenTelemetry integration
class HaystackAction(Action):
    """Burr ``Action`` wrapping a Haystack ``Component``.

    Haystack ``Component`` is the basic block of a Haystack ``Pipeline``.
    A ``Component`` is instantiated, then it receives inputs for its ``.run()`` method
    and returns output values.

    Learn more about components here: https://docs.haystack.deepset.ai/docs/custom-components
    """

    def __init__(
        self,
        component: Component,
        reads: Union[list[str], dict[str, str]],
        writes: Union[list[str], dict[str, str]],
        name: Optional[str] = None,
        bound_params: Optional[dict] = None,
    ):
        """Create a Burr ``Action`` from a Haystack ``Component``.

        :param component: Haystack ``Component`` to wrap
        :param reads: State fields read and passed to ``Component.run()``
        :param writes: State fields where results of ``Component.run()`` are written
        :param name: Name of the action. Can be set later via ``.with_name()`` or in the
            ``ApplicationBuilder``.
        :param bound_params: Parameters to bind to the `Component.run()` method.

        Basic example:

        .. code-block:: python

            from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
            from haystack.document_stores.in_memory import InMemoryDocumentStore
            from burr.core import ApplicationBuilder
            from burr.integrations.haystack import HaystackAction

            retrieve_documents = HaystackAction(
                component=InMemoryEmbeddingRetriever(InMemoryDocumentStore()),
                name="retrieve_documents",
                reads=["query_embedding"],
                writes=["documents"],
            )

            app = (
              ApplicationBuilder()
              .with_actions(retrieve_documents)
              .with_transitions("retrieve_documents", "retrieve_documents")
              .with_entrypoint("retrieve_documents")
              .build()
            )
        """
        self._component = component
        self._name = name
        self._bound_params = bound_params if bound_params is not None else {}

        # NOTE input and output socket mappings are kept separately to avoid naming conflicts.
        if isinstance(reads, Mapping):
            self._input_socket_mapping = reads
            self._reads = list(set(reads.values()))
        elif isinstance(reads, Sequence):
            self._input_socket_mapping = {socket_name: socket_name for socket_name in reads}
            self._reads = reads
        else:
            raise TypeError(f"`reads` must be a sequence or mapping. Received: {type(reads)}")

        self._validate_input_sockets()

        if isinstance(writes, Mapping):
            self._output_socket_mapping = writes
            self._writes = list(writes.keys())
        elif isinstance(writes, Sequence):
            self._output_socket_mapping = {socket_name: socket_name for socket_name in writes}
            self._writes = writes
        else:
            raise TypeError(f"`writes` must be a sequence or mapping. Received: {type(writes)}")

        self._validate_output_sockets()

    def _validate_input_sockets(self) -> None:
        component_inputs = self._component.__haystack_input__._sockets_dict.keys()
        for socket_name in self._input_socket_mapping.keys():
            if socket_name not in component_inputs:
                raise ValueError(
                    f"Socket `{socket_name}` not found in `Component` inputs: {component_inputs}"
                )

    def _validate_output_sockets(self) -> None:
        component_outputs = self._component.__haystack_output__._sockets_dict.keys()
        for socket_name in self._output_socket_mapping.values():
            if socket_name not in component_outputs:
                raise ValueError(
                    f"Socket `{socket_name}` not found in `Component` outputs: {component_outputs}"
                )

    @property
    def component(self) -> Component:
        """Haystack `Component` used by this action."""
        return self._component

    @property
    def reads(self) -> list[str]:
        """State fields read and passed to `Component.run()`"""
        return self._reads

    @property
    def writes(self) -> list[str]:
        """State fields where results of `Component.run()` are written."""
        return self._writes

    @property
    def inputs(self) -> tuple[dict[str, str], dict[str, str]]:
        """Return dictionaries of required and optional inputs for `Component.run()`"""
        required_inputs, optional_inputs = {}, {}
        for socket_name, input_socket in self._component.__haystack_input__._sockets_dict.items():
            state_field_name = self._input_socket_mapping.get(socket_name, socket_name)

            # if we expect the value to come from state (previous actions) or it's a
            # bound parameter, then this socket isn't a user-provided input
            if state_field_name in self.reads or state_field_name in self._bound_params:
                continue

            # determine if input is required or optional based on the socket's default value
            if input_socket.default_value == haystack_empty:
                required_inputs[state_field_name] = input_socket.type
            else:
                optional_inputs[state_field_name] = input_socket.type

        return required_inputs, optional_inputs

    def run(self, state: State, **run_kwargs) -> dict[str, Any]:
        """Call the Haystack `Component.run()` method.

        :param state: State object of the application. It contains some input values
           for ``Component.run()``.
        :param run_kwargs: User-provided inputs for ``Component.run()``.
        :return: Dictionary of results with mapping ``{socket_name: value}``.

        Note, values come from 3 sources:
        - state (from previous actions)
        - run_kwargs (inputs from ``Application.run()``)
        - bound parameters (from ``HaystackAction`` instantiation)
        """
        values = {}

        # here, precedence matters. Alternatively, we could unpack all dictionaries at once
        # which would throw an error for key collisions
        for input_socket_name, value in self._bound_params.items():
            values[input_socket_name] = value

        for input_socket_name, state_field_name in self._input_socket_mapping.items():
            try:
                values[input_socket_name] = state[state_field_name]
            except KeyError as e:
                raise ValueError(f"No value found in state for field: {state_field_name}") from e

        for input_socket_name, value in run_kwargs.items():
            values[input_socket_name] = value

        return self._component.run(**values)

    def update(self, result: dict, state: State) -> State:
        """Update the state using the results of ``Component.run()``.
        The output socket name is mapped to the Burr state field name.

        Values returned by ``Component.run()`` that aren't in ``writes`` are ignored.
        """
        # TODO we could want to handle ``.update()`` and ``.append()`` differently
        state_update = {}

        for state_field_name, output_socket_name in self._output_socket_mapping.items():
            if state_field_name in self.writes:
                try:
                    state_update[state_field_name] = result[output_socket_name]
                except KeyError as e:
                    raise ValueError(
                        f"Socket `{output_socket_name}` missing from output of `Component.run()`"
                    ) from e
        print(state_update)
        return state.update(**state_update)

    def get_source(self) -> str:
        """Return the source code of the Haystack ``Component``.

        NOTE. This doesn't include the initialization parameters of the ``Component``.
        This can be obtained using``HaystackAction().component.to_dict()``, but this
        method might is not implemented for all components.
        """
        return inspect.getsource(self._component.__class__)


def _socket_name_mapping(sockets_connections: list[tuple[str, str]]) -> dict[str, str]:
    """Map socket names to a single socket name.

    In Haystack, components communicate via sockets. A socket called
    "embedding" in one component can be renamed to "query_embedding" when
    passed to another component.

    In Burr, there is a single state object so we need a mapping to resolve
    that `embedding` and `query_embedding` point to the same value. This function
    creates a mapping {socket_name: state_field} to rename sockets when creating
    the Burr `Graph`.
    """
    all_connections: dict[str, set[str]] = {}
    for from_, to in sockets_connections:
        if from_ not in all_connections:
            all_connections[from_] = {from_}
        all_connections[from_].add(to)

        if to not in all_connections:
            all_connections[to] = {to}
        all_connections[to].add(from_)

    reduced_mapping: dict[str, str] = {}
    for key, values in all_connections.items():
        unique_name = min(values)
        reduced_mapping[key] = unique_name

    return reduced_mapping


def _connected_inputs(pipeline) -> dict[str, list[str]]:
    """Get all input sockets that are connected to other components."""
    return {
        name: [
            socket.name
            for socket in data.get("input_sockets", {}).values()
            if socket.is_variadic or socket.senders
        ]
        for name, data in pipeline.graph.nodes(data=True)
    }


def _connected_outputs(pipeline) -> dict[str, list[str]]:
    """Get all output sockets that are connected to other components."""
    return {
        name: [
            socket.name for socket in data.get("output_sockets", {}).values() if socket.receivers
        ]
        for name, data in pipeline.graph.nodes(data=True)
    }


def haystack_pipeline_to_burr_graph(pipeline: Pipeline) -> Graph:
    """Convert a Haystack `Pipeline` to a Burr `Graph`.

    NOTE. This currently doesn't support Haystack pipelines with
    parallel branches. Learn more https://docs.haystack.deepset.ai/docs/pipelines#branching

    From the Haystack `Pipeline`, we can easily retrieve transitions.
    For actions, we need to create `HaystackAction` from components
    and map their sockets to Burr state fields

    EXPERIMENTAL: This feature is experimental and may change in the future.
    Changes to Haystack or Burr could impact this function. Please let us know if
    you encounter any issues.
    """

    # get all socket connections in the pipeline
    sockets_connections = [
        (edge_data["from_socket"].name, edge_data["to_socket"].name)
        for _, _, edge_data in pipeline.graph.edges.data()
    ]
    socket_mapping = _socket_name_mapping(sockets_connections)

    transitions = [(from_, to) for from_, to, _ in pipeline.graph.edges]

    # get all input and output sockets that are connected to other components
    connected_inputs = _connected_inputs(pipeline)
    connected_outputs = _connected_outputs(pipeline)

    actions = []
    for component_name, component in pipeline.walk():
        inputs_mapping = {
            socket_name: socket_mapping[socket_name]
            for socket_name in connected_inputs[component_name]
        }
        outputs_mapping = {
            socket_mapping[socket_name]: socket_name
            for socket_name in connected_outputs[component_name]
        }

        haystack_action = HaystackAction(
            name=component_name,
            component=component,
            reads=inputs_mapping,
            writes=outputs_mapping,
        )
        actions.append(haystack_action)

    return GraphBuilder().with_actions(*actions).with_transitions(*transitions).build()
