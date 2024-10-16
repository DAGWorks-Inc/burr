from typing import Any, Optional, Union

from haystack import Pipeline
from haystack.core.component import Component
from haystack.core.component.types import _empty as haystack_empty

from burr.core.action import Action
from burr.core.graph import Graph, GraphBuilder
from burr.core.state import State


class HaystackAction(Action):
    """Create a Burr `Action` from a Haystack `Component`."""

    def __init__(
        self,
        component: Component,
        reads: Union[list[str], dict[str, str]],
        writes: Union[list[str], dict[str, str]],
        name: Optional[str] = None,
        bound_params: Optional[dict] = None,
    ):
        """
        Notes
        - need to figure out how to use bind
        - you can use `action.bind()` to set values of `Component.run()`.
        """
        self._component = component
        self._name = name
        self._reads = list(reads.keys()) if isinstance(reads, dict) else reads
        self._writes = list(writes.values()) if isinstance(writes, dict) else writes
        self._bound_params = bound_params if bound_params is not None else {}

        self._socket_mapping = {}
        if isinstance(reads, dict):
            for state_field, socket_name in reads.items():
                self._socket_mapping[socket_name] = state_field

        if isinstance(writes, dict):
            for socket_name, state_field in writes.items():
                self._socket_mapping[socket_name] = state_field

    @property
    def reads(self) -> list[str]:
        return self._reads

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def inputs(self) -> tuple[dict[str, str], dict[str, str]]:
        """Return dictionaries of required and optional inputs."""
        required_inputs, optional_inputs = {}, {}
        for socket_name, input_socket in self._component.__haystack_input__._sockets_dict.items():
            state_field_name = self._socket_mapping.get(socket_name, socket_name)

            if state_field_name in self.reads:
                continue
            elif state_field_name in self._bound_params:
                continue

            if input_socket.default_value == haystack_empty:
                required_inputs[state_field_name] = input_socket.type
            else:
                optional_inputs[state_field_name] = input_socket.type

        return required_inputs, optional_inputs

    def run(self, state: State, **run_kwargs) -> dict[str, Any]:
        """Call the Haystack `Component.run()` method. It returns a dictionary
        of results with mapping {socket_name: value}.

        Values come from 3 sources:
        - bound parameters (from HaystackAction instantiation, or by using `.bind()`)
        - state (from previous actions)
        - run_kwargs (inputs from `Application.run()`)
        """
        values = {}

        # here, precedence matters. Alternatively, we could unpack all dictionaries at once
        # which would throw an error for key collisions
        for param, value in self._bound_params.items():
            values[param] = value

        for param in self.reads:
            values[param] = state[param]

        for param, value in run_kwargs.keys():
            values[param] = value

        return self._component.run(**values)

    def update(self, result: dict, state: State) -> State:
        """Update the state using the results of `Component.run()`."""
        state_update = {}
        for socket_name, value in result.items():
            state_field_name = self._socket_mapping.get(socket_name, socket_name)
            if state_field_name in self.writes:
                state_update[state_field_name] = value

        return state.update(**state_update)

    def bind(self, **kwargs):
        """Bind a parameter for the `Component.run()` call."""
        self._bound_params.update(**kwargs)
        return self


def _socket_name_mapping(pipeline) -> dict[str, str]:
    """Map socket names to a single state field name.

    In Haystack, components communicate via sockets. A socket called
    "embedding" in one component can be renamed to "query_embedding" when
    passed to another component.

    In Burr, there is a single state object so we need a mapping to resolve
    that `embedding` and `query_embedding` point to the same value. This function
    creates a mapping {socket_name: state_field} to rename sockets when creating
    the Burr `Graph`.
    """
    sockets_connections = [
        (edge_data["from_socket"].name, edge_data["to_socket"].name)
        for _, _, edge_data in pipeline.graph.edges.data()
    ]
    mapping = {}

    for from_, to in sockets_connections:
        if from_ not in mapping:
            mapping[from_] = {from_}
        mapping[from_].add(to)

        if to not in mapping:
            mapping[to] = {to}
        mapping[to].add(from_)

    result = {}
    for key, values in mapping.items():
        unique_name = min(values)
        result[key] = unique_name

    return result


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

    From the Haystack `Pipeline`, we can easily retrieve transitions.
    For actions, we need to create `HaystackAction` from components
    and map their sockets to Burr state fields
    """
    socket_mapping = _socket_name_mapping(pipeline)
    connected_inputs = _connected_inputs(pipeline)
    connected_outputs = _connected_outputs(pipeline)

    transitions = [(from_, to) for from_, to, _ in pipeline.graph.edges]

    actions = []
    for component_name, component in pipeline.walk():
        inputs_from_state = [
            socket_mapping[socket_name] for socket_name in connected_inputs[component_name]
        ]
        outputs_to_state = [
            socket_mapping[socket_name] for socket_name in connected_outputs[component_name]
        ]

        haystack_action = HaystackAction(
            name=component_name,
            component=component,
            reads=inputs_from_state,
            writes=outputs_to_state,
        )
        actions.append(haystack_action)

    return GraphBuilder().with_actions(*actions).with_transitions(*transitions).build()
