import collections
import dataclasses
import logging
from typing import Any, AsyncGenerator, Generator, List, Literal, Optional, Set, Tuple, Union

from burr.core.action import Action, Condition, Function, Reducer, default
from burr.core.state import State
from burr.lifecycle.base import LifecycleAdapter
from burr.lifecycle.internal import LifecycleAdapterSet

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Transition:
    """Internal, utility class"""

    from_: Action
    to: Action
    condition: Condition


TerminationCondition = Literal["any_complete", "all_complete"]

PRIOR_STEP = "__PRIOR_STEP"


def _run_function(function: Function, state: State) -> dict:
    """Runs a function, returning the result of running the function.
    Note this restricts the keys in the state to only those that the
    function reads.

    :param function:
    :param state:
    :return:
    """
    if function.is_async():
        raise ValueError(
            f"Cannot run async: {function} "
            "in non-async context. Use astep()/aiterate()/arun() "
            "instead...)"
        )
    state_to_use = state.subset(*function.reads)
    return function.run(state_to_use)


async def _arun_function(function: Function, state: State) -> dict:
    """Runs a function, returning the result of running the function.
    Async version of the above.

    :param function:
    :param state:
    :return:
    """
    state_to_use = state.subset(*function.reads)
    return await function.run(state_to_use)


def _run_reducer(reducer: Reducer, state: State, result: dict, name: str) -> State:
    """Runs the reducer, returning the new state. Note this restricts the
    keys in the state to only those that the function writes.

    :param reducer:
    :param state:
    :param result:
    :return:
    """
    state_to_use = state.subset(*reducer.writes)
    new_state = reducer.update(result, state_to_use)
    keys_in_new_state = set(new_state.keys())
    extra_keys = keys_in_new_state - set(reducer.writes)
    if extra_keys:
        raise ValueError(
            f"Action {name} attempted to write to keys {extra_keys} "
            f"that it did not declare. It declared: ({reducer.writes})!"
        )
    return state.merge(new_state.update(**{PRIOR_STEP: name}))


class Application:
    def __init__(
        self,
        actions: List[Action],
        transitions: List[Transition],
        state: State,
        initial_step: str,
        adapter_set: Optional[LifecycleAdapterSet] = None,
    ):
        self._action_map = {action.name: action for action in actions}
        self._adjacency_map = Application._create_adjacency_map(transitions)
        self._transitions = transitions
        self._actions = actions
        self._initial_step = initial_step
        self._state = state
        self._adapter_set = adapter_set if adapter_set is not None else LifecycleAdapterSet()

    def step(self) -> Optional[Tuple[Action, dict, State]]:
        """Performs a single step, advancing the state machine along.
        This returns a tuple of the action that was run, the result of running
        the action, and the new state.

        Use this if you just want to do something with the state and not rely on generators.
        E.G. press forward/backwards, hnuman in the loop, etc... Odds are this is not
         the method you want -- you'll want iterate() (if you want to see the state/
        results along the way), or run() (if you just want the final state/results).

        :return: Tuple[Function, dict, State] -- the function that was just ran, the result of running it, and the new state
        """
        next_action = self.get_next_action()
        self._adapter_set.call_all_lifecycle_hooks_sync(
            "pre_run_step", action=next_action, state=self._state
        )
        if next_action is None:
            return None
        exc = None
        result = None
        new_state = self._state
        try:
            result = _run_function(next_action, self._state)
            new_state = _run_reducer(next_action, self._state, result, next_action.name)
            self._set_state(new_state)
        except Exception as e:
            exc = e
            raise e
        finally:
            self._adapter_set.call_all_lifecycle_hooks_sync(
                "post_run_step", action=next_action, state=new_state, result=result, exception=exc
            )
        return next_action, result, new_state

    async def astep(self) -> Optional[Tuple[Action, dict, State]]:
        """Asynchronous version of step.

        :return:
        """
        next_action = self.get_next_action()
        if next_action is None:
            return None
        await self._adapter_set.call_all_lifecycle_hooks_async(
            "pre_run_step", action=next_action, state=self._state
        )
        exc = None
        result = None
        new_state = self._state
        try:
            if not next_action.is_async():
                # we can just delegate to the synchronous version, it will block the event loop,
                # but that's safer than assuming its OK to launch a thread
                # TODO -- add an option/configuration to launch a thread (yikes, not super safe, but for a pure function
                # which this is supposed to be its OK).
                # this delegatees hooks to the synchronous version, so we'll call all of them as well
                return self.step()
            result = await _arun_function(next_action, self._state)
            new_state = _run_reducer(next_action, self._state, result, next_action.name)
        except Exception as e:
            exc = e
            raise e
        finally:
            await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
                "post_run_step", action=next_action, state=new_state, result=result, exception=exc
            )
        self._set_state(new_state)
        return next_action, result, new_state

    def iterate(
        self, *, until: list[str], gate: TerminationCondition = "any_complete"
    ) -> Generator[Tuple[Action, dict, State], None, Tuple[State, List[dict]]]:
        """Returns a generator that calls step() in a row, enabling you to see the state
        of the system as it updates. Note this returns a generator, and also the final result
        (for convenience).

        :param until: The list of actions to run until -- these must be strings
            that match the names of the actions.
        :param gate: The gate to run until. This can be "any_complete" or "all_complete"
        :return: Each iteration returns the result of running `step`
            The final result is the current state + results in the order that they were specified.
        """

        if gate != "any_complete":
            raise NotImplementedError(
                "Only any_complete is supported for now -- "
                "please reach out to the developers to unblock other gate types!"
            )

        results: List[Optional[dict]] = [None for _ in until]
        index_by_name = {name: index for index, name in enumerate(until)}
        seen_results = set()

        condition = (
            lambda: any(item in seen_results for item in until)
            if gate == "any_complete"
            else lambda: len(seen_results) == len(until)
        )

        while not condition():
            result = self.step()
            if result is None:
                break
            action, result, state = result
            if action.name in until:
                seen_results.add(action.name)
                results[index_by_name[action.name]] = result
            yield action, result, state
        return self._state, results

    async def aiterate(
        self, *, until: list[str], gate: TerminationCondition = "any_complete"
    ) -> AsyncGenerator[Tuple[Action, dict, State], Tuple[State, List[dict]]]:
        """Returns a generator that calls step() in a row, enabling you to see the state
        of the system as it updates. This is the asynchronous version so it has no capability of t

        :param until: The list of actions to run until -- these must be strings
            that match the names of the action.
        :param gate: The gate to run until. This can be "any_complete" or "all_complete"
        :return: Each iteration returns the result of running `step`
            The final result is the current state + results in the order that they were specified.
        """

        seen_results = set()
        condition = (
            lambda: any(item in seen_results for item in until)
            if gate == "any_complete"
            else lambda: len(seen_results) == len(until)
        )

        while not condition():
            result = await self.astep()
            if result is None:
                break
            action, result, state = result
            if action.name in until:
                seen_results.add(action.name)
            yield action, result, state

    def run(
        self,
        *,
        until: list[str],
        gate: TerminationCondition = "any_complete",
    ) -> Tuple[State, List[dict]]:
        """

        :param gate:
        :param until:
        :return:
        """
        gen = self.iterate(until=until, gate=gate)
        while True:
            try:
                next(gen)
            except StopIteration as e:
                return e.value

    async def arun(
        self,
        *,
        until: list[str],
        gate: TerminationCondition = "any_complete",
    ):
        """Asynchronous version of run.

        :param gate:
        :param until:
        :return:
        """
        state = self._state
        results: List[Optional[dict]] = [None for _ in until]
        index_by_name = {name: index for index, name in enumerate(until)}
        async for action, result, state in self.aiterate(until=until, gate=gate):
            if action.name in until:
                results[index_by_name[action.name]] = result
        return state, results

    def visualize(
        self,
        output_file_path: str,
        include_conditions: bool = False,
        include_state: bool = False,
        view: bool = False,
        **graphviz_kwargs: Any,
    ):
        try:
            import graphviz  # noqa: F401
        except ModuleNotFoundError:
            logger.exception(
                " graphviz is required for visualizing the application graph. Install it with:"
                '\n\n  pip install "burr[visualization]" or pip install graphviz \n\n'
            )
            return
        digraph_attr = dict(
            graph_attr=dict(
                rankdir="TB",
                ranksep="0.4",
                compound="false",
                concentrate="false",
            ),
        )
        for g_key, g_value in graphviz_kwargs.items():
            if isinstance(g_value, dict):
                digraph_attr[g_key].update(**g_value)
            else:
                digraph_attr[g_key] = g_value
        digraph = graphviz.Digraph(**digraph_attr)
        for action in self._actions:
            label = (
                action.name
                if not include_state
                else f"{action.name}({', '.join(action.reads)}): {', '.join(action.writes)}"
            )
            digraph.node(action.name, label=label, shape="box", style="rounded")
        for transition in self._transitions:
            condition = transition.condition
            digraph.edge(
                transition.from_.name,
                transition.to.name,
                label=condition.name if include_conditions and condition is not default else None,
                style="dashed" if transition.condition is not default else "solid",
            )
        digraph.render(output_file_path, view=view)
        return digraph

    @staticmethod
    def _create_adjacency_map(transitions: List[Transition]) -> dict:
        adjacency_map = collections.defaultdict(list)
        for transition in transitions:
            from_ = transition.from_
            to = transition.to
            adjacency_map[from_.name].append((to.name, transition.condition))
        return adjacency_map

    def _set_state(self, new_state: State):
        self._state = new_state

    def get_next_action(self) -> Optional[Action]:
        if PRIOR_STEP not in self._state:
            return self._action_map[self._initial_step]
        possibilities = self._adjacency_map[self._state[PRIOR_STEP]]
        for next_action, condition in possibilities:
            if condition.run(self._state)[Condition.KEY]:
                return self._action_map[next_action]
        return None

    def update_state(self, new_state: State):
        """Updates state -- this is meant to be called if you need to do
        anything with the state. For example:
        1. Reset it (after going through a loop)
        2. Store to some external source/log out

        :param new_state:
        :return:
        """
        self._state = new_state

    @property
    def state(self) -> State:
        """Gives the state. Recall that state is purely immutable
        -- anything you do with this state will not be persisted unless you
        subsequently call update_state.

        :return: The current state object.
        """
        return self._state

    @property
    def actions(self) -> List[Action]:
        return self._actions


def _assert_set(value: Optional[Any], field: str, method: str):
    if value is None:
        raise ValueError(
            f"Must set {field} before building application! Do so with ApplicationBuilder.{method}"
        )


def _validate_transitions(
    transitions: Optional[List[Tuple[str, str, Condition]]], actions: Set[str]
):
    _assert_set(transitions, "_transitions", "with_transitions")
    exhausted = {}  # items for which we have seen a default transition
    for from_, to, condition in transitions:
        if from_ not in actions:
            raise ValueError(
                f"Transition source: {from_} not found in actions! "
                f"Please add to actions using with_actions({from_}=...)"
            )
        if to not in actions:
            raise ValueError(
                f"Transition target: {to} not found in actions! "
                f"Please add to actions using with_actions({to}=...)"
            )
        if condition.name == "default":  # we have seen a default transition
            if from_ in exhausted:
                raise ValueError(
                    f"Transition {from_} -> {to} is redundant -- "
                    f"a default transition has already been set for {from_}"
                )
            exhausted[from_] = True
    return True


def _validate_start(start: Optional[str], actions: Set[str]):
    _assert_set(start, "_start", "with_entrypoint")
    if start not in actions:
        raise ValueError(
            f"Entrypoint: {start} not found in actions. Please add "
            f"using with_actions({start}=...)"
        )


def _validate_actions(actions: Optional[List[Action]]):
    _assert_set(actions, "_actions", "with_actions")
    if len(actions) == 0:
        raise ValueError("Must have at least one action in the application!")


@dataclasses.dataclass
class ApplicationBuilder:
    state: State = dataclasses.field(default_factory=State)
    transitions: List[Tuple[str, str, Condition]] = None
    actions: List[Action] = None
    start: str = None
    lifecycle_adapters: List[LifecycleAdapter] = dataclasses.field(default_factory=list)

    def with_state(self, **kwargs) -> "ApplicationBuilder":
        if self.state is not None:
            self.state = self.state.update(**kwargs)
        else:
            self.state = State(kwargs)
        return self

    def with_entrypoint(self, action: str) -> "ApplicationBuilder":
        """Adds an entrypoint to the application. This is the action that will be run first.
        This can only be called once.

        :param action:
        :return:
        """
        # TODO -- validate only called once
        self.start = action
        return self

    def with_actions(self, **actions: Action) -> "ApplicationBuilder":
        """Adds an action to the application. The actions are granted names (using the with_name)
        method post-adding, using the kw argument. Thus, this is the only supported way to add actions.

        :param actions: Actions to add, keyed by name
        :return: The application builder for future chaining.
        """
        if self.actions is None:
            self.actions = []
        for key, value in actions.items():
            self.actions.append(value.with_name(key))
        return self

    def with_transitions(
        self,
        *transitions: Union[
            Tuple[Union[str, list[str]], str], Tuple[Union[str, list[str]], str, Condition]
        ],
    ) -> "ApplicationBuilder":
        """Adds transitions to the application. Transitions are specified as tuples of either:
            1. (from, to, condition)
            2. (from, to)  -- condition is set to DEFAULT (which is a fallback)

        Transitions will be evaluated in order of specification -- if one is met, the others will not be evaluated.
        Note that one transition can be terminal -- the system doesn't have


        :param transitions: Transitions to add
        :return: The application builder for future chaining.
        """
        if self.transitions is None:
            self.transitions = []
        for transition in transitions:
            from_, to_, *conditions = transition
            if len(conditions) > 0:
                condition = conditions[0]
            else:
                condition = default
            if not isinstance(from_, list):
                from_ = [from_]
            for action in from_:
                if not isinstance(action, str):
                    raise ValueError(f"Transition source must be a string, not {action}")
                if not isinstance(to_, str):
                    raise ValueError(f"Transition target must be a string, not {to_}")
                self.transitions.append((action, to_, condition))
        return self

    def with_hooks(self, *adapters: LifecycleAdapter) -> "ApplicationBuilder":
        """Adds a lifecycle adapter to the application. This is a way to add hooks to the application so that
        they are run at the appropriate times. You can use this to synchronize state out, log results, etc...

        :param adapter: Adapter to add
        :return: The application builder for future chaining.
        """
        self.lifecycle_adapters.extend(adapters)
        return self

    def build(self) -> Application:
        _validate_actions(self.actions)
        actions_by_name = {action.name: action for action in self.actions}
        all_actions = set(actions_by_name.keys())
        _validate_transitions(self.transitions, all_actions)
        _validate_start(self.start, all_actions)
        return Application(
            actions=self.actions,
            transitions=[
                Transition(
                    from_=actions_by_name[from_],
                    to=actions_by_name[to],
                    condition=condition,
                )
                for from_, to, condition in self.transitions
            ],
            state=self.state,
            initial_step=self.start,
            adapter_set=LifecycleAdapterSet(*self.lifecycle_adapters),
        )
