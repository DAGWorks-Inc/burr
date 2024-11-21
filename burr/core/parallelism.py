import abc
import asyncio
import dataclasses
import inspect
from typing import Any, AsyncGenerator, Callable, Dict, Generator, List, Tuple, TypeVar, Union

from burr.core import Action, Application, ApplicationBuilder, ApplicationContext, Graph, State
from burr.core.action import SingleStepAction
from burr.core.graph import GraphBuilder

SubgraphType = Union[Action, Callable, "RunnableGraph"]


@dataclasses.dataclass
class RunnableGraph:
    """Contains a graph with information it needs to run.
    This is a bit more than a graph -- we have entrypoints + halt_after points.
    This is the core element of a recursive action -- your recursive generators can yield these
    (as well as actions/functions, which both get turned into single-node graphs...)
    """

    graph: Graph
    entrypoint: str
    halt_after: List[str]

    @staticmethod
    def create(from_: SubgraphType) -> "RunnableGraph":
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
    """Task to run a subgraph. Has runtime-spefici information, like inputs, state, and
    the application ID. This is the lower-level component -- the user will only directly interact
    with this if they use the TaskBasedParallelAction interface, which produces a generator of these.
    """

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
            # TODO -- handle persistence...
            .with_identifiers(
                app_id=self.application_id,
                partition_key=parent_context.partition_key,  # cascade the partition key
            )
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
    """The base class for actions that run a set of tasks in parallel and reduce the results.
    This is more power-user mode -- if you need fine-grained control over the set of tasks
    your parallel action utilizes, then this is for you. If not, you'll want to see:

    - :py:class:`MapActionsAndStates` -- a cartesian product of actions/states
    - :py:class:`MapActions` -- a map of actions over a single state
    - :py:class:`MapStates` -- a map of a single action over multiple states

    If you're unfamiliar about where to start, you'll want to see the docs on :ref:`parallelism <parallelism>`.

    This is responsible for two things:

    1. Creating a set of tasks to run in parallel
    2. Reducing the results of those tasks into a single state for the action to return.

    The following example shows how to call a set of prompts over a set of different models in parallel and return the result.

    .. code-block:: python

        from burr.core import action, state, ApplicationContext
        from burr.core.parallelism import MapStates, RunnableGraph
        from typing import Callable, Generator, List

        @action(reads=["prompt", "model"], writes=["llm_output"])
        def query_llm(state: State, model: str) -> State:
            # TODO -- implement _query_my_llm to call litellm or something
            return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

        class MultipleTaskExample(TaskBasedParallelAction):
            def tasks(state: State, context: ApplicationContext) -> Generator[SubGraphTask, None, None]:
                for prompt in state["prompts"]:
                    for action in [
                        query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                        query_llm.bind(model="o1").with_name("o1_answer"),
                        query_llm.bind(model="claude").with_name("claude_answer"),
                    ]
                        yield SubGraphTask(
                            action=action, # can be a RunnableGraph as well
                            state=state.update(prompt=prompt),
                            inputs={},
                            # stable hash -- up to you to ensure uniqueness
                            application_id=hashlib.sha256(context.application_id + action.name + prompt).hexdigest(),
                            # a few other parameters we might add -- see advanced usage -- failure conditions, etc...
                        )

            def reduce(self, states: Generator[State, None, None]) -> State:
                all_llm_outputs = []
                for state in states:
                    all_llm_outputs.append(
                        {
                            "output" : state["llm_output"],
                            "model" : state["model"],
                            "prompt" : state["prompt"],
                        }
                    )
                return state.update(all_llm_outputs=all_llm_outputs)
    """

    def __init__(self):
        super().__init__()

    def run_and_update(self, state: State, **run_kwargs) -> Tuple[dict, State]:
        """Runs and updates. This is not user-facing, so do not override it.
        This runs all actions in parallel (using the supplied executor, from the context),
        and then reduces the results.

        :param state: Input state
        :param run_kwargs: Additional inputs (runtime inputs)
        :return: The results, updated state tuple. The results are empty, but we may add more in the future.
        """

        def _run_and_update():
            context: ApplicationContext = run_kwargs.get("__context")
            if context is None:
                raise ValueError("This action requires a context to run")
            state_without_internals = state.wipe(
                delete=[item for item in state.keys() if item.startswith("__")]
            )
            task_generator = self.tasks(state_without_internals, context, run_kwargs)

            def execute_task(task):
                return task.run(run_kwargs["__context"])

            with context.parallel_executor_factory() as executor:
                # Directly map the generator to the executor
                results = list(executor.map(execute_task, task_generator))

            def state_generator() -> Generator[Any, None, None]:
                yield from results

            return {}, self.reduce(state_without_internals, state_generator())

        async def _arun_and_update():
            context: ApplicationContext = run_kwargs.get("__context")
            if context is None:
                raise ValueError("This action requires a context to run")
            state_without_internals = state.wipe(
                delete=[item for item in state.keys() if item.startswith("__")]
            )
            task_generator = self.tasks(state_without_internals, context, run_kwargs)

            # TODO -- run in parallel
            async def state_generator():
                """This makes it easier on the user -- if they don't have an async generator we can still exhause it
                This way we run through all of the task generators. These correspond to the task generation capabilities above (the map*/task generation stuff)
                """
                if inspect.isasyncgen(task_generator):
                    coroutines = [task.arun(context) async for task in task_generator]
                else:
                    coroutines = [task.arun(context) for task in task_generator]
                results = await asyncio.gather(*coroutines)
                # TODO -- yield in order...
                for result in results:
                    yield result

            return {}, await self.reduce(state_without_internals, state_generator())

        if self.is_async():
            return _arun_and_update()  # type: ignore
        return _run_and_update()

    def is_async(self) -> bool:
        """This says whether or not the action is async. Note you have to override this if you have async tasks
        and want to use asyncio.gather on them. Otherwise leave this blank.

        :return: Whether or not the action is async
        """
        return False

    @property
    def inputs(self) -> Union[list[str], tuple[list[str], list[str]]]:
        """Inputs from this -- if you want to override you'll want to call super()
        first so you get these inputs.

        :return: the list of inputs that will populate kwargs.
        """
        return ["__context"]  # TODO -- add any additional input

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
    """Base class to run a cartesian product of actions x states.

    For example, if you want to run the following:

    - n prompts
    - m models

    This will make it easy to do. If you need fine-grained control, you can use the :py:class:`TaskBasedParallelAction`,
    which allows you to specify the tasks individually. If you just want to vary actions/states  (and not both), use
    :py:class:`MapActions` or :py:class:`MapStates` implementations.

    The following shows how to run a set of prompts over a set of models in parallel and return the results.

    .. code-block:: python

        from burr.core import action, state
        from burr.core.parallelism import MapActionsAndStates, RunnableGraph
        from typing import Callable, Generator, List

        @action(reads=["prompt", "model"], writes=["llm_output"])
        def query_llm(state: State, model: str) -> State:
            # TODO -- implement _query_my_llm to call litellm or something
            return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

        class TestModelsOverPrompts(MapActionsAndStates):

            def actions(self, state: State) -> Generator[Action | Callable | RunnableGraph, None, None]:
                # make sure to add a name to the action
                # This is not necessary for subgraphs, as actions will already have names
                for action in [
                    query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                    query_llm.bind(model="o1").with_name("o1_answer"),
                    query_llm.bind(model="claude").with_name("claude_answer"),
                ]:
                    yield action

            def states(self, state: State) -> Generator[State, None, None]:
                for prompt in [
                    "What is the meaning of life?",
                    "What is the airspeed velocity of an unladen swallow?",
                    "What is the best way to cook a steak?",
                ]:
                    yield state.update(prompt=prompt)

            def reduce(self, states: Generator[State, None, None]) -> State:
                all_llm_outputs = []
                for state in states:
                    all_llm_outputs.append(
                        {
                            "output" : state["llm_output"],
                            "model" : state["model"],
                            "prompt" : state["prompt"],
                        }
                    )
                return state.update(all_llm_outputs=all_llm_outputs)

            @property
            def reads(self) -> list[str]:
                return ["prompts"]

            @property
            def writes(self) -> list[str]:
                return ["all_llm_outputs"]

    """

    @abc.abstractmethod
    def actions(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubgraphType, None, None]:
        """Yields actions to run in parallel. These will be merged with the states as a cartesian product.

        :param state: Input state at the time of running the "parent" action.
        :param inputs: Runtime Inputs to the action
        :return: Generator of actions to run
        """
        pass

    @abc.abstractmethod
    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Yields states to run in parallel. These will be merged with the actions as a cartesian product.

        :param state: Input state at the time of running the "parent" action.
        :param context: Context for the action
        :param inputs: Runtime Inputs to the action
        :return: Generator of states to run
        """
        pass

    def tasks(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubGraphTask, None, None]:
        """Takes the cartesian product of actions and states, creating tasks for each.

        :param state: Input state at the time of running the "parent" action.
        :param context: Context for the action
        :param inputs: Runtime Inputs to the action
        :return: Generator of tasks to run
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

        :param states: State outputs from the subtasks
        :return: Reduced state
        """
        pass


class MapActions(MapActionsAndStates, abc.ABC):
    """Base class to run a set of actions over the same state. Actions can be functions (decorated with @action),
    action objects, or subdags implemented as :py:class:`RunnableGraph` objects. With this, you can do the following:

    1. Specify the actions to run
    2. Specify the state to run the actions over
    3. Reduce the results into a single state

    This is useful, for example, to run different LLMs over the same set of prompts,

    Here is an example (with some pseudocode) of doing just that:

    .. code-block:: python

        from burr.core import action, state
        from burr.core.parallelism import MapActions, RunnableGraph
        from typing import Callable, Generator, List

        @action(reads=["prompt", "model"], writes=["llm_output"])
        def query_llm(state: State, model: str) -> State:
            # TODO -- implement _query_my_llm to call litellm or something
            return state.update(llm_output=_query_my_llm(prompt=state["prompt"], model=model))

        class TestMultipleModels(MapActions):

            def actions(self, state: State) -> Generator[Action | Callable | RunnableGraph, None, None]:
                # Make sure to add a name to the action if you use bind() with a function,
                # note that these can be different actions, functions, etc...
                # in this case we're using `.bind()` to create multiple actions, but we can use some mix of
                # subgraphs, functions, action objects, etc...
                for action in [
                    query_llm.bind(model="gpt-4").with_name("gpt_4_answer"),
                    query_llm.bind(model="o1").with_name("o1_answer"),
                    query_llm.bind(model="claude").with_name("claude_answer"),
                ]:
                    yield action

            def state(self, state: State) -> State:
                return state.update(prompt="What is the meaning of life?")

            def reduce(self, states: Generator[State, None, None]) -> State:
                all_llm_outputs = []
                for state in states:
                    all_llm_outputs.append(state["llm_output"])
                return state.update(all_llm_outputs=all_llm_outputs)

            @property
            def reads(self) -> List[str]:
                return ["prompt"] # we're just running this on a single prompt, for multiple actions

            @property
            def writes(self) -> List[str]:
                return ["all_llm_outputs"]

    """

    @abc.abstractmethod
    def actions(
        self, state: State, inputs: Dict[str, Any], context: ApplicationContext
    ) -> Generator[SubgraphType, None, None]:
        """Gives all actions to map over, given the state/inputs.

        :param state: State at the time of running the action
        :param inputs: Runtime Inputs to the action
        :param context: Context for the action
        :return: Generator of actions to run
        """

    @abc.abstractmethod
    def state(self, state: State, inputs: Dict[str, Any]):
        """Gives the state for each of the actions

        :param state: State at the time of running the action
        :param inputs: Runtime inputs to the action
        :return: State for the action
        """
        pass

    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Just converts the state into a generator of 1, so we can use the superclass. This is internal."""
        yield self.state(state, inputs)

    @abc.abstractmethod
    def reduce(self, state: State, states: Generator[State, None, None]) -> State:
        """Reduces the task's results into a single state. Runs through all outputs
        and combines them together, to form the final state for the action.

        :param states: State outputs from the subtasks
        :return: Reduced state
        """
        pass


class MapStates(MapActionsAndStates, abc.ABC):
    """Base class to run a single action over a set of states. States are given as
    updates (manipulations) of the action's input state, specified by the `states`
    generator.

    With this, you can do the following:

    1. Specify the states to run
    2. Specify the action to run over all the states
    3. Reduce the results into a single state

    This is useful, for example, to run different prompts over the same LLM,

    Here is an example (with some pseudocode) of doing just that:

    .. code-block:: python

        from burr.core import action, state
        from burr.core.parallelism import MapStates, RunnableGraph
        from typing import Callable, Generator, List

        @action(reads=["prompt"], writes=["llm_output"])
        def query_llm(state: State) -> State:
            return state.update(llm_output=_query_my_llm(prompt=state["prompt"]))

        class TestMultiplePrompts(MapStates):

            def action(self) -> Action | Callable | RunnableGraph:
                # make sure to add a name to the action
                # This is not necessary for subgraphs, as actions will already have names
                return query_llm.with_name("query_llm")

            def states(self, state: State) -> Generator[State, None, None]:
                # You could easily have a list_prompts upstream action that writes to "prompts" in state
                # And loop through those
                # This hardcodes for simplicity
                for prompt in [
                    "What is the meaning of life?",
                    "What is the airspeed velocity of an unladen swallow?",
                    "What is the best way to cook a steak?",
                ]:
                    yield state.update(prompt=prompt)


            def reduce(self, states: Generator[State, None, None]) -> State:
                all_llm_outputs = []
                for state in states:
                    all_llm_outputs.append(state["llm_output"])
                return state.update(all_llm_outputs=all_llm_outputs)

            @property
            def reads(self) -> List[str]:
                return ["prompts"]

            @property
            def writes(self) -> List[str]:
                return ["all_llm_outputs"]
    """

    @abc.abstractmethod
    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        """Generates all states to map over, given the state and inputs.
        Each state will be an update to the input state.

        For instance, you may want to take an input state that has a list field, and expand it
        into a set of states, each with a different value from the list.

        For example:

        .. code-block:: python

            def states(self, state: State, context: ApplicationContext, inputs: Dict[str, Any]) -> Generator[State, None, None]:
                for item in state["multiple_fields"]:
                    yield state.update(individual_field=item)

        :param state: Initial state
        :param context: Context for the action
        :param inputs: Runtime inputs to the action
        :return: Generator of states to run
        """
        pass

    @abc.abstractmethod
    def action(self, state: State, inputs: Dict[str, Any]) -> SubgraphType:
        """The single action to apply to each state.
        This can be a function (decorated with `@action`, action object, or subdag).

        :param state: State to run the action over
        :param inputs: Runtime inputs to the action
        :return: Action to run
        """
        pass

    def actions(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubgraphType, None, None]:
        """Maps the action over each state generated by the `states` method.
        Internally used, do not implement."""
        yield self.action(state, inputs)

    @abc.abstractmethod
    def reduce(self, state: State, results: Generator[State, None, None]) -> State:
        """Reduces the task's results

        :param results:
        :return:
        """
        pass


GenType = TypeVar("GenType")
ReturnType = TypeVar("ReturnType")

SyncOrAsyncGenerator = Union[Generator[GenType, None, None], AsyncGenerator[GenType, None]]
SyncOrAsyncGeneratorOrItemOrList = Union[SyncOrAsyncGenerator[GenType], List[GenType], GenType]


class PassThroughMapActionsAndStates(MapActionsAndStates):
    def __init__(
        self,
        action: Union[
            SubgraphType,
            List[SubgraphType],
            Callable[
                [State, ApplicationContext, Dict[str, Any]], SyncOrAsyncGenerator[SubgraphType]
            ],
        ],
        state: Callable[[State, ApplicationContext, Dict[str, Any]], SyncOrAsyncGenerator[State]],
        reducer: Callable[[State, SyncOrAsyncGenerator[State]], State],
        reads: List[str],
        writes: List[str],
        inputs: List[str],
    ):
        super().__init__()
        self._action_or_generator = action
        self._state_or_generator = state
        self._reducer = reducer
        self._reads = reads
        self._writes = writes
        self._inputs = inputs

    def actions(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[SubgraphType, None, None]:
        if isinstance(self._action_or_generator, list):
            for action in self._action_or_generator:
                yield action
            return
        if isinstance(self._action_or_generator, SubgraphType):
            yield self._action_or_generator
        else:
            gen = self._action_or_generator(state, context, inputs)
            if inspect.isasyncgen(gen):

                async def gen():
                    async for item in self._action_or_generator(state, context, inputs):
                        yield item

                return gen()
            else:
                yield from self._action_or_generator(state, context, inputs)

    def states(
        self, state: State, context: ApplicationContext, inputs: Dict[str, Any]
    ) -> Generator[State, None, None]:
        gen = self._state_or_generator(state, context, inputs)
        if isinstance(gen, State):
            yield gen
        if inspect.isasyncgen(gen):

            async def gen():
                async for item in self._state_or_generator(state, context, inputs):
                    yield item

            return gen()
        else:
            yield from gen

    def reduce(self, state: State, states: SyncOrAsyncGenerator[State]) -> State:
        return self._reducer(state, states)

    @property
    def writes(self) -> list[str]:
        return self._writes

    @property
    def reads(self) -> list[str]:
        return self._reads


def map_reduce_action(
    # action: Optional[SubgraphType]=None,
    action: Union[
        SubgraphType,
        List[SubgraphType],
        Callable[
            [State, ApplicationContext, Dict[str, Any]],
            SyncOrAsyncGeneratorOrItemOrList[SubgraphType],
        ],
    ],
    state: Callable[
        [State, ApplicationContext, Dict[str, Any]], SyncOrAsyncGeneratorOrItemOrList[State]
    ],
    reducer: Callable[[State, SyncOrAsyncGenerator[State]], State],
    reads: List[str],
    writes: List[str],
    inputs: List[str],
):
    """Experimental API for creating a map-reduce action easily. We'll be improving this."""
    return PassThroughMapActionsAndStates(
        action=action, state=state, reducer=reducer, reads=reads, writes=writes, inputs=inputs
    )
