import abc
import dataclasses
from typing import Any, Callable, Dict, Generator, List, Tuple, Union

from burr.core import Action, Application, ApplicationBuilder, ApplicationContext, Graph, State
from burr.core.action import SingleStepAction
from burr.core.graph import GraphBuilder


class Executor:
    ...


@dataclasses.dataclass
class RunnableGraph:
    """Contains a graph with information it needs to run.
    This is a bit more than a graph -- we have entrypoints + halt_after points."""

    graph: Graph
    entrypoint: str
    halt_after: List[str]

    @staticmethod
    def create(from_: Union[Callable, Action, "RunnableGraph"]) -> "RunnableGraph":
        """Creates a RunnableGraph from a callable/action. This will create a single-node runnable graph,
        so we can wrap it up in a task.

        :param from_: Callable or Action to wrap
        :return: RunnableGraph
        """
        if isinstance(from_, RunnableGraph):
            return from_
        if isinstance(from_, Action):
            assert (
                from_.name is not None
            ), "Action must have a name to be run, internal error, reach out to devs"
        graph = GraphBuilder().with_actions(from_).build()
        (action,) = graph.actions
        return RunnableGraph(graph=graph, entrypoint=action.name, halt_after=[action.name])


@dataclasses.dataclass
class SubGraphTask:
    graph: RunnableGraph
    inputs: Dict[str, Any]
    state: State
    application_id: str

    def _create_app(self, parent_context: ApplicationContext) -> Application:
        return (
            ApplicationBuilder()
            .with_graph(self.graph.graph)
            .with_entrypoint(self.graph.entrypoint)
            .with_state(self.state)
            .with_spawning_parent(
                app_id=parent_context.app_id,
                sequence_id=parent_context.sequence_id,
                partition_key=parent_context.partition_key,
            )
            .with_tracker(parent_context.tracker.copy())  # We have to copy
            .build()
        )

    def run(
        self,
        parent_context: ApplicationContext,
    ) -> State:
        """Runs the task -- this simply executes it b y instantiating a sub-application"""
        app = self._create_app(parent_context)
        action, result, state = app.run(
            halt_after=self.graph.halt_after,
            inputs={key: value for key, value in self.inputs.items() if not key.startswith("__")},
        )
        return state

    async def arun(self, parent_context: ApplicationContext):
        app = self._create_app(parent_context)
        action, result, state = await app.arun(
            halt_after=self.graph.halt_after,
            inputs={key: value for key, value in self.inputs.items() if not key.startswith("__")},
        )
        return state


def _stable_app_id_hash(app_id: str, child_key: str) -> str:
    """Gives a stable hash for an application. Given the parent app_id and a child key,
    this will give a hash that will be stable across runs.

    :param app_id:
    :param additional_key:
    :return:
    """
    ...


class TaskBasedParallelAction(SingleStepAction):
    def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        """Runs and updates. TODO -- run in parallel!

        :param state:
        :param run_kwargs:
        :return:
        """
        context: ApplicationContext = run_kwargs.get("__context")
        if context is None:
            raise ValueError("This action requires a context to run")
        state_without_internals = state.wipe(
            delete=[item for item in state.keys() if item.startswith("__")]
        )
        task_generator = self.tasks(state_without_internals, context, run_kwargs)

        # TODO -- run in parallel
        def state_generator():
            for task in task_generator:
                yield task.run(run_kwargs["__context"])

        return {}, self.reduce(state_without_internals, state_generator())

    @property
    def inputs(self) -> Union[list[str], tuple[list[str], list[str]]]:
        return ["__context"]  # TODO -- add any additional input

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def tasks(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubGraphTask, None, None]:
        """Creates all tasks that this action will run, given the state/inputs.
        This produces a generator of SubGraphTasks that will be run in parallel.

        :param state: State prior to action's execution
        :param context: Context for the action
        :yield: SubGraphTasks to run
        """
        pass

    @abc.abstractmethod
    def reduce(self, state: State, states: Generator[State, None, None]) -> State:
        """Reduces the states from the tasks into a single state.

        :param states: State outputs from the subtasks
        :return: Reduced state
        """
        pass

    @property
    @abc.abstractmethod
    def writes(self) -> list[str]:
        pass

    @property
    @abc.abstractmethod
    def reads(self) -> list[str]:
        pass


class MapActionsAndStates(TaskBasedParallelAction):
    @abc.abstractmethod
    def actions(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[Union[Action, Callable, RunnableGraph], None, None]:
        """Yields actions to run in parallel. These will be merged with the states as a cartesian product.

        :param state:
        :param inputs:
        :return:
        """
        pass

    @abc.abstractmethod
    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Yields states to run in parallel

        :param state:
        :param context:
        :param inputs:
        :return:
        """
        pass

    def tasks(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubGraphTask, None, None]:
        """Takes the cartesian product of actions and states, creating tasks for each.

        :param state:
        :param context:
        :param inputs:
        :return:
        """
        for i, action in enumerate(self.actions(state, context, inputs)):
            for j, state in enumerate(self.states(state, context, inputs)):
                key = f"{i}-{j}"  # this is a stable hash for now but will not handle caching
                # TODO -- allow for custom hashes that will indicate stability (user is responsible)
                yield SubGraphTask(
                    graph=RunnableGraph.create(action),
                    inputs=inputs,
                    state=state,
                    application_id=_stable_app_id_hash(context.app_id, key),
                )

    @abc.abstractmethod
    def reduce(self, state: State, states: Generator[State, None, None]) -> State:
        """Reduces the states from the tasks into a single state.

        :param states:
        :return:
        """
        pass


class MapActions(MapActionsAndStates, abc.ABC):
    @abc.abstractmethod
    def actions(
        self, state: State, inputs: Dict[str, Any], context: ApplicationContext
    ) -> Generator[Union[Action, Callable, RunnableGraph], None, None]:
        """Gives all actions to map over, given the state/inputs

        :param state:
        :param inputs:
        :param context:
        :return:
        """

    @abc.abstractmethod
    def state(self, state: State, inputs: Dict[str, Any]):
        """Gives the state for each of the actions

        :param state:
        :param inputs:
        :return:
        """
        pass

    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Just converts the state into a generator of 1, so we can use the superclass"""
        yield self.state(state, inputs)

    @abc.abstractmethod
    def reduce(self, state: State, states: Generator[State, None, None]) -> State:
        """Reduces the task's results

        :param states:
        :return:
        """
        pass


class MapStates(MapActionsAndStates, abc.ABC):
    @abc.abstractmethod
    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Generates all states to map over, given the state and inputs

        :param state:
        :param context:
        :param inputs:
        :return:
        """
        pass

    @abc.abstractmethod
    def action(
        self, state: State, inputs: Dict[str, Any]
    ) -> Union[Action, Callable, RunnableGraph]:
        """The single action to apply to each state

        :param state:
        :param inputs:
        :return:
        """
        pass

    def actions(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[Union[Action, Callable, RunnableGraph], None, None]:
        """Maps the action over each state generated by the `states` method

        :param state:
        :param context:
        :param inputs:
        :return:
        """
        for sub_state in self.states(state, context, inputs):
            yield self.action(sub_state, inputs)

    @abc.abstractmethod
    def reduce(self, state: State, results: Generator[State, None, None]) -> State:
        """Reduces the task's results

        :param results:
        :return:
        """
        pass
