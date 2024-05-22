import collections
import dataclasses
import functools
import inspect
import logging
import pprint
import uuid
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from burr import telemetry, visibility
from burr.common import types as burr_types
from burr.core import persistence
from burr.core.action import (
    Action,
    AsyncStreamingAction,
    AsyncStreamingResultContainer,
    Condition,
    Function,
    Reducer,
    SingleStepAction,
    SingleStepStreamingAction,
    StreamingAction,
    StreamingResultContainer,
    create_action,
    default,
)
from burr.core.persistence import BaseStateLoader, BaseStateSaver
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


PRIOR_STEP = "__PRIOR_STEP"
SEQUENCE_ID = "__SEQUENCE_ID"

ERROR_MESSAGE = (
    "-------------------------------------------------------------------\n"
    "Oh no an error! Need help with Burr?\n"
    "Join our discord and ask for help! https://discord.gg/4FxBMyzW5n\n"
    "-------------------------------------------------------------------\n"
)


def _validate_result(result: dict, name: str) -> None:
    if not isinstance(result, dict):
        raise ValueError(
            f"Action {name} returned a non-dict result: {result}. "
            f"All results must be dictionaries."
        )


def _run_function(function: Function, state: State, inputs: Dict[str, Any], name: str) -> dict:
    """Runs a function, returning the result of running the function.
    Note this restricts the keys in the state to only those that the
    function reads.

    :param function: Function to run
    :param state: State at time of execution
    :param inputs: Inputs to the function
    :return:
    """
    if function.is_async():
        raise ValueError(
            f"Cannot run async: {name} "
            "in non-async context. Use astep()/aiterate()/arun() "
            "instead...)"
        )
    state_to_use = state.subset(*function.reads)
    function.validate_inputs(inputs)
    result = function.run(state_to_use, **inputs)
    _validate_result(result, name)
    return result


async def _arun_function(
    function: Function, state: State, inputs: Dict[str, Any], name: str
) -> dict:
    """Runs a function, returning the result of running the function.
    Async version of the above."""
    state_to_use = state.subset(*function.reads)
    function.validate_inputs(inputs)
    result = await function.run(state_to_use, **inputs)
    _validate_result(result, name)
    return result


def _state_update(state_to_modify: State, modified_state: State) -> State:
    """This is a hack to apply state updates and ensure that we are respecting deletions. Specifically, the process is:

    1. We subset the state to what we want to read
    2. We perform a set of state-specific writes to it
    3. We measure which ones were deleted
    4. We then merge the whole state back in
    5. We then delete the keys that were deleted

    This is suboptimal -- we should not be observing the state, we should be using the state commands and layering in deltas.
    That said, we currently eagerly evaluate the state at all operations, which means we have to do it this way. See
    https://github.com/DAGWorks-Inc/burr/issues/33 for a more details plan.

    This function was written to solve this issue: https://github.com/DAGWorks-Inc/burr/issues/28.


    :param state_subset_pre_update: The subset of state passed to the update() function
    :param modified_state: The subset of state realized after the update() function
    :param state_to_modify: The state to modify-- this is the original
    :return:
    """
    old_state_keys = set(state_to_modify.keys())
    new_state_keys = set(modified_state.keys())
    deleted_keys = list(old_state_keys - new_state_keys)
    # TODO -- unify the logic of choosing whether a key is internal or not
    # Right now this is __sequence_id and __prior_step, but it could be more
    deleted_keys_filtered = [item for item in deleted_keys if not item.startswith("__")]
    return state_to_modify.merge(modified_state).wipe(delete=deleted_keys_filtered)


def _validate_reducer_writes(reducer: Reducer, state: State, name: str) -> None:
    required_writes = reducer.writes
    missing_writes = set(reducer.writes) - state.keys()
    if len(missing_writes) > 0:
        raise ValueError(
            f"State is missing write keys after running: {name}. Missing keys are: {missing_writes}. "
            f"Has writes: {required_writes}"
        )


def _run_reducer(reducer: Reducer, state: State, result: dict, name: str) -> State:
    """Runs the reducer, returning the new state. Note this restricts the
    keys in the state to only those that the function writes.

    :param reducer:
    :param state:
    :param result:
    :return:
    """
    # TODO -- better guarding on state reads/writes
    new_state = reducer.update(result, state)
    keys_in_new_state = set(new_state.keys())
    new_keys = keys_in_new_state - set(state.keys())
    extra_keys = new_keys - set(reducer.writes)
    if len(extra_keys) > 0:
        raise ValueError(
            f"Action {name} attempted to write to keys {extra_keys} "
            f"that it did not declare. It declared: ({reducer.writes})!"
        )
    _validate_reducer_writes(reducer, new_state, name)
    return _state_update(state, new_state)


def _create_dict_string(kwargs: dict) -> str:
    """This is a utility function to create a string representation of a dict.
    This is the state that was passed into the function usually. This is useful for debugging,
    as it can be printed out to see what the state was.

    :param kwargs: The inputs to the function that errored.
    :return: The string representation of the inputs, truncated appropriately.
    """
    pp = pprint.PrettyPrinter(width=80)
    inputs = {}
    for k, v in kwargs.items():
        item_repr = repr(v)
        if len(item_repr) > 50:
            item_repr = item_repr[:50] + "..."
        else:
            item_repr = v
        inputs[k] = item_repr
    input_string = pp.pformat(inputs)
    if len(input_string) > 1000:
        input_string = input_string[:1000] + "..."
    return input_string


def _format_error_message(action: Action, input_state: State, inputs: dict) -> str:
    """Formats the error string, given that we're inside an action"""
    message = ERROR_MESSAGE
    message += f"> Action: `{action.name}` encountered an error!"
    padding = " " * (80 - len(message) - 1)
    message += padding + "<"
    message += "\n> State (at time of action):\n" + _create_dict_string(input_state.get_all())
    message += "\n> Inputs (at time of action):\n" + _create_dict_string(inputs)
    border = "*" * 80
    return "\n" + border + "\n" + message + "\n" + border


def _run_single_step_action(
    action: SingleStepAction, state: State, inputs: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], State]:
    """Runs a single step action. This API is internal-facing and a bit in flux, but
    it corresponds to the SingleStepAction class.

    :param action: Action to run
    :param state: State to run with
    :param inputs: Inputs to pass directly to the action
    :return: The result of running the action, and the new state
    """
    # TODO -- guard all reads/writes with a subset of the state
    action.validate_inputs(inputs)
    result, new_state = action.run_and_update(state, **inputs)
    _validate_result(result, action.name)
    out = result, _state_update(state, new_state)
    _validate_result(result, action.name)
    _validate_reducer_writes(action, new_state, action.name)
    return out


def _run_single_step_streaming_action(
    action: SingleStepStreamingAction, state: State, inputs: Optional[Dict[str, Any]]
) -> Generator[Tuple[dict, Optional[State]], None, None]:
    """Runs a single step streaming action. This API is internal-facing.
    This normalizes + validates the output."""
    action.validate_inputs(inputs)
    generator = action.stream_run_and_update(state, **inputs)
    result = None
    state_update = None
    for item in generator:
        if not isinstance(item, tuple):
            # TODO -- consider adding support for just returning a result.
            raise ValueError(
                f"Action {action.name} must yield a tuple of (result, state_update). "
                f"For all non-final results (intermediate),"
                f"the state update must be None"
            )
        result, state_update = item
        if state_update is None:
            yield result, None
    if state_update is None:
        raise ValueError(
            f"Action {action.name} did not return a state update. For streaming actions, the last yield "
            f"statement must be a tuple of (result, state_update). For example, yield dict(foo='bar'), state.update(foo='bar')"
        )
    _validate_result(result, action.name)
    _validate_reducer_writes(action, state_update, action.name)
    yield result, state_update


async def _arun_single_step_streaming_action(
    action: SingleStepStreamingAction, state: State, inputs: Optional[Dict[str, Any]]
) -> AsyncGenerator[Tuple[dict, Optional[State]], None]:
    """Runs a single step streaming action in async. See the synchronous version for more details."""
    action.validate_inputs(inputs)
    generator = action.stream_run_and_update(state, **inputs)
    result = None
    state_update = None
    async for item in generator:
        if not isinstance(item, tuple):
            # TODO -- consider adding support for just returning a result.
            raise ValueError(
                f"Action {action.name} must yield a tuple of (result, state_update). "
                f"For all non-final results (intermediate),"
                f"the state update must be None"
            )
        result, state_update = item
        if state_update is None:
            yield result, None
    if state_update is None:
        raise ValueError(
            f"Action {action.name} did not return a state update. For async actions, the last yield "
            f"statement must be a tuple of (result, state_update). For example, yield dict(foo='bar'), state.update(foo='bar')"
        )
    _validate_result(result, action.name)
    _validate_reducer_writes(action, state_update, action.name)
    # TODO -- add guard against zero-length stream
    yield result, state_update


def _run_multi_step_streaming_action(
    action: StreamingAction, state: State, inputs: Optional[Dict[str, Any]]
) -> Generator[Tuple[dict, Optional[State]], None, None]:
    """Runs a multi-step streaming action. E.G. one with a run/reduce step.
    This API is internal-facing. Note that this converts the shape of a
    multi-step streaming action to yielding the results of the run step
    as well as the state update, which is None for all the finaly ones.

    This peeks ahead by one so we know when this is done (and when to validate).
    """
    action.validate_inputs(inputs)
    generator = action.stream_run(state, **inputs)
    result = None
    for item in generator:
        # We want to peek ahead so we can return the last one
        # This is slightly eager, but only in the case in which we
        # are using a multi-step streaming action
        next_result = result
        result = item
        if next_result is not None:
            yield next_result, None
    state_update = _run_reducer(action, state, result, action.name)
    _validate_result(result, action.name)
    _validate_reducer_writes(action, state_update, action.name)
    yield result, state_update


async def _arun_multi_step_streaming_action(
    action: AsyncStreamingAction, state: State, inputs: Optional[Dict[str, Any]]
) -> AsyncGenerator[Tuple[dict, Optional[State]], None]:
    """Runs a multi-step streaming action in async. See the synchronous version for more details."""
    action.validate_inputs(inputs)
    generator = action.stream_run(state, **inputs)
    result = None
    async for item in generator:
        # We want to peek ahead so we can return the last one
        # This is slightly eager, but only in the case in which we
        # are using a multi-step streaming action
        next_result = result
        result = item
        if next_result is not None:
            yield next_result, None
    state_update = _run_reducer(action, state, result, action.name)
    _validate_result(result, action.name)
    _validate_reducer_writes(action, state_update, action.name)
    yield result, state_update


async def _arun_single_step_action(
    action: SingleStepAction, state: State, inputs: Optional[Dict[str, Any]]
) -> Tuple[dict, State]:
    """Runs a single step action in async. See the synchronous version for more details."""
    state_to_use = state
    action.validate_inputs(inputs)
    result, new_state = await action.run_and_update(state_to_use, **inputs)
    _validate_result(result, action.name)
    _validate_reducer_writes(action, new_state, action.name)
    return result, _state_update(state, new_state)


@dataclasses.dataclass
class ApplicationGraph:
    """User-facing representation of the state machine. This has

    #. All the action objects
    #. All the transition objects
    #. The entrypoint action
    """

    actions: List[Action]
    transitions: List[Transition]
    entrypoint: Action


class Application:
    def __init__(
        self,
        actions: List[Action],
        transitions: List[Transition],
        state: State,
        initial_step: str,
        partition_key: Optional[str],
        uid: str,
        sequence_id: Optional[int] = None,
        adapter_set: Optional[LifecycleAdapterSet] = None,
        builder: Optional["ApplicationBuilder"] = None,
        parent_pointer: Optional[burr_types.ParentPointer] = None,
    ):
        """Instantiates an Application. This is an internal API -- use the builder!

        :param actions: Actions to run
        :param transitions: Transitions between actions
        :param state: State to run with
        :param initial_step: Step name to start at
        :param partition_key: Partition key for the application (optional)
        :param uid: Unique identifier for the application
        :param sequence_id: Sequence ID for the application. Note this will be incremented every run.
            So if this starts at 0, the first one you will see will be 1.
        :param adapter_set: Set of lifecycle adapters
        :param builder: Builder that created this application
        """
        self._partition_key = partition_key
        self._uid = uid
        self._action_map = {action.name: action for action in actions}
        self._adjacency_map = Application._create_adjacency_map(transitions)
        self._transitions = transitions
        self._actions = actions
        self._initial_step = initial_step
        self._state = state
        self._adapter_set = adapter_set if adapter_set is not None else LifecycleAdapterSet()
        self._graph = self._create_graph()
        self._adapter_set.call_all_lifecycle_hooks_sync(
            "post_application_create",
            state=self._state,
            application_graph=self._graph,
            app_id=self._uid,
            partition_key=self._partition_key,
            parent_pointer=parent_pointer,
        )
        # TODO -- consider adding global inputs + global input factories to the builder
        self.dependency_factory = {
            "__tracer": functools.partial(
                visibility.tracing.TracerFactory, lifecycle_adapters=self._adapter_set
            )
        }
        if sequence_id is not None:
            self._set_sequence_id(sequence_id)
        self._builder = builder
        self._parent_pointer = parent_pointer

    # @telemetry.capture_function_usage # todo -- capture usage when we break this up into one that isn't called internally
    # This will be doable when we move sequence ID to the beginning of the function https://github.com/DAGWorks-Inc/burr/pull/73
    def step(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Tuple[Action, dict, State]]:
        """Performs a single step, advancing the state machine along.
        This returns a tuple of the action that was run, the result of running
        the action, and the new state.

        Use this if you just want to do something with the state and not rely on generators.
        E.G. press forward/backwards, human in the loop, etc... Odds are this is not
        the method you want -- you'll want iterate() (if you want to see the state/
        results along the way), or run() (if you just want the final state/results).

        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world
        :return: Tuple[Function, dict, State] -- the function that was just ran, the result of running it, and the new state
        """
        # we need to increment the sequence before we start computing
        # that way if we're replaying from state, we don't get stuck
        self._increment_sequence_id()
        out = self._step(inputs=inputs, _run_hooks=True)
        return out

    def _step(
        self, inputs: Optional[Dict[str, Any]], _run_hooks: bool = True
    ) -> Optional[Tuple[Action, dict, State]]:
        """Internal-facing version of step. This is the same as step, but with an additional
        parameter to hide hook execution so async can leverage it."""
        next_action = self.get_next_action()
        if next_action is None:
            return None
        if inputs is None:
            inputs = {}
        action_inputs = self._process_inputs(inputs, next_action)
        if _run_hooks:
            self._adapter_set.call_all_lifecycle_hooks_sync(
                "pre_run_step",
                action=next_action,
                state=self._state,
                inputs=action_inputs,
                sequence_id=self.sequence_id,
                app_id=self._uid,
                partition_key=self._partition_key,
            )
        exc = None
        result = None
        new_state = self._state
        try:
            if next_action.single_step:
                result, new_state = _run_single_step_action(next_action, self._state, action_inputs)
            else:
                result = _run_function(
                    next_action, self._state, action_inputs, name=next_action.name
                )
                new_state = _run_reducer(next_action, self._state, result, next_action.name)

            new_state = self._update_internal_state_value(new_state, next_action)
            self._set_state(new_state)
        except Exception as e:
            exc = e
            logger.exception(_format_error_message(next_action, self._state, inputs))
            raise e
        finally:
            if _run_hooks:
                self._adapter_set.call_all_lifecycle_hooks_sync(
                    "post_run_step",
                    app_id=self._uid,
                    partition_key=self._partition_key,
                    action=next_action,
                    state=new_state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=exc,
                )
        return next_action, result, new_state

    def reset_to_entrypoint(self) -> None:
        """Resets the state machine to the entrypoint action."""
        self._set_state(self._state.wipe(delete=[PRIOR_STEP]))

    def _update_internal_state_value(self, new_state: State, next_action: Action) -> State:
        """Updates the internal state values of the new state."""
        new_state = new_state.update(
            **{
                PRIOR_STEP: next_action.name,
            }
        )
        return new_state

    def _process_inputs(self, inputs: Dict[str, Any], action: Action) -> Dict[str, Any]:
        inputs = inputs.copy()
        processed_inputs = {}
        required_inputs, optional_inputs = action.optional_and_required_inputs
        for key in list(inputs.keys()):
            if key in required_inputs or key in optional_inputs:
                processed_inputs[key] = inputs.pop(key)
        if len(inputs) > 0 and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Keys {inputs.keys()} were passed in as inputs to action "
                f"{action.name}, but not declared by the action as an input. "
                f"Action only needs: {required_inputs} (optionally: {optional_inputs}) "
                f"so we're just letting you know some inputs are being skipped."
            )
        missing_inputs = required_inputs - set(processed_inputs.keys())
        for required_input in list(missing_inputs):
            # if we can find it in the dependency factory, we'll use that
            if required_input in self.dependency_factory:
                processed_inputs[required_input] = self.dependency_factory[required_input](
                    action, self.sequence_id
                )
                missing_inputs.remove(required_input)
        if len(missing_inputs) > 0:
            missing_inputs_dict = {key: "FILL ME IN" for key in missing_inputs}
            missing_inputs_dict.update({key: "..." for key in inputs.keys()})
            addendum = (
                "\nPlease double check the values passed to the keyword argument `inputs` to however you're running "
                "the burr application.\n"
                "e.g.\n"
                f"   app.run( # or app.step, app.iterate, app.astep, etc.\n"
                f"       halt_..., # your halt logic\n"
                f"       inputs={missing_inputs_dict}  # <-- this is what you need to adjust\n"
                f"   )"
            )
            raise ValueError(
                f"Action {action.name} is missing required inputs: {missing_inputs}. "
                f"Has inputs: {processed_inputs}. " + addendum
            )
        return processed_inputs

    # @telemetry.capture_function_usage
    # ditto with step()
    async def astep(self, inputs: Dict[str, Any] = None) -> Optional[Tuple[Action, dict, State]]:
        """Asynchronous version of step.

        :param inputs: Inputs to the action -- this is if this action
            requires an input that is passed in from the outside world

        :return: Tuple[Function, dict, State] -- the action that was just ran, the result of running it, and the new state
        """
        self._increment_sequence_id()
        out = await self._astep(inputs=inputs, _run_hooks=True)
        return out

    async def _astep(self, inputs: Optional[Dict[str, Any]], _run_hooks: bool = True):
        # we want to increment regardless of failure
        next_action = self.get_next_action()
        if next_action is None:
            return None
        if inputs is None:
            inputs = {}
        action_inputs = self._process_inputs(inputs, next_action)
        if _run_hooks:
            await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
                "pre_run_step",
                action=next_action,
                state=self._state,
                inputs=action_inputs,
                sequence_id=self.sequence_id,
                app_id=self._uid,
                partition_key=self._partition_key,
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
                # this delegates hooks to the synchronous version, so we'll call all of them as well
                return self._step(
                    inputs=action_inputs, _run_hooks=False
                )  # Skip hooks as we already ran all of them/will run all of them in this function's finally
            if next_action.single_step:
                result, new_state = await _arun_single_step_action(
                    next_action, self._state, inputs=action_inputs
                )
            else:
                result = await _arun_function(
                    next_action, self._state, inputs=action_inputs, name=next_action.name
                )
                new_state = _run_reducer(next_action, self._state, result, next_action.name)
            new_state = self._update_internal_state_value(new_state, next_action)
            self._set_state(new_state)
        except Exception as e:
            exc = e
            logger.exception(_format_error_message(next_action, self._state, inputs))
            raise e
        finally:
            if _run_hooks:
                await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
                    "post_run_step",
                    action=next_action,
                    state=new_state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=exc,
                    app_id=self._uid,
                    partition_key=self._partition_key,
                )

        return next_action, result, new_state

    def _clean_iterate_params(
        self,
        halt_before: list[str] = None,
        halt_after: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[list[str], list[str], Dict[str, Any]]:
        """Utility function to clean out iterate params so we have less duplication between iterate/aiterate
        and the logic is cleaner later.
        """
        if halt_before is None and halt_after is None:
            logger.warning(
                "No halt termination specified -- this has the possibility of running forever!"
            )
        if halt_before is None:
            halt_before = []
        if halt_after is None:
            halt_after = []
        if inputs is None:
            inputs = {}
        return halt_before, halt_after, inputs

    def _validate_halt_conditions(self, halt_before: list[str], halt_after: list[str]) -> None:
        """Utility function to validate halt conditions"""
        missing_actions = set(halt_before + halt_after) - set(self._action_map.keys())
        if len(missing_actions) > 0:
            raise ValueError(
                ERROR_MESSAGE
                + f"Halt conditions {missing_actions} are not registered actions. Please ensure that they have been "
                f"registered as actions in the application and that you've spelled them correctly!"
                f"Valid actions are: {self._action_map.keys()}"
            )

    def has_next_action(self) -> bool:
        """Returns whether or not there is a next action to run.

        :return: True if there is a next action, False otherwise
        """
        return self.get_next_action() is not None

    def _should_halt_iterate(
        self, halt_before: list[str], halt_after: list[str], prior_action: Action
    ) -> bool:
        """Internal utility function to determine whether or not to halt during iteration"""
        if self.has_next_action() and self.get_next_action().name in halt_before:
            logger.debug(f"Halting before executing {self.get_next_action().name}")
            return True
        elif prior_action.name in halt_after:
            logger.debug(f"Halting after executing {prior_action.name}")
            return True
        return False

    def _return_value_iterate(
        self,
        halt_before: list[str],
        halt_after: list[str],
        prior_action: Optional[Action],
        result: Optional[dict],
    ) -> Tuple[Optional[Action], Optional[dict], State]:
        """Utility function to decide what to return for iterate/arun. Note that run() will delegate to the return value of
        iterate, whereas arun cannot delegate to the return value of aiterate (as async generators cannot return a value).
        We put the code centrally to clean up the logic.
        """
        if self.has_next_action() and self.get_next_action().name in halt_before:
            logger.debug(
                f"We have hit halt_before condition with next action: {self.get_next_action().name}. "
                f"Returning: next_action={self.get_next_action()}, None, and state"
            )
            return self.get_next_action(), None, self._state
        if prior_action is not None and prior_action.name in halt_after:
            prior_action_name = prior_action.name if prior_action is not None else None
            logger.debug(
                f"We have hit halt_after condition with prior action: {prior_action_name}. "
                f"Returning: prior_action={prior_action}, result, and state"
            )
            return prior_action, result, self._state
        logger.warning(
            "This is trying to return without having computed a single action -- "
            "we'll end up just returning some Nones. This means that nothing was executed "
            "(E.G. that the state machine had nowhere to go). Either fix the state machine or"
            f"the halt conditions, or both... Halt conditions are: halt_before={halt_before}, halt_after={halt_after}."
            f"Note that this is considered undefined behavior -- if you get here, you should fix!"
        )
        return prior_action, result, self._state

    @telemetry.capture_function_usage
    def iterate(
        self,
        *,
        halt_before: list[str] = None,
        halt_after: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Generator[Tuple[Action, dict, State], None, Tuple[Action, Optional[dict], State]]:
        """Returns a generator that calls step() in a row, enabling you to see the state
        of the system as it updates. Note this returns a generator, and also the final result
        (for convenience).

        Note the nuance with halt_before and halt_after. halt_before conditions will take precedence to halt_after. Furthermore,
        a single iteration will always be executed prior to testing for any halting conditions.

        :param halt_before: The list of actions to halt before execution of. It will halt prior to the execution of the first one it sees.
        :param halt_after: The list of actions to halt after execution of. It will halt after the execution of the first one it sees.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world.
            Note that this is only used for the first iteration -- subsequent iterations will not use this.
        :return: Each iteration returns the result of running `step`. This generator also returns a tuple of
            [action, result, current state]
        """
        halt_before, halt_after, inputs = self._clean_iterate_params(
            halt_before, halt_after, inputs
        )
        self._validate_halt_conditions(halt_before, halt_after)

        result = None
        prior_action: Optional[Action] = None
        while self.has_next_action():
            # self.step will only return None if there is no next action, so we can rely on tuple unpacking
            prior_action, result, state = self.step(inputs=inputs)
            yield prior_action, result, state
            if self._should_halt_iterate(halt_before, halt_after, prior_action):
                break
        return self._return_value_iterate(halt_before, halt_after, prior_action, result)

    @telemetry.capture_function_usage
    async def aiterate(
        self,
        *,
        halt_before: list[str] = None,
        halt_after: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Tuple[Action, dict, State], None]:
        """Returns a generator that calls step() in a row, enabling you to see the state
        of the system as it updates. This is the asynchronous version so it has no capability of t

        :param halt_before: The list of actions to halt before execution of. It will halt on the first one.
        :param halt_after: The list of actions to halt after execution of. It will halt on the first one.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world.
            Note that this is only used for the first iteration -- subsequent iterations will not use this.
        :return: Each iteration returns the result of running `step`. This returns nothing -- it's an async generator which is not
            allowed to have a return value.
        """
        halt_before, halt_after, inputs = self._clean_iterate_params(
            halt_before, halt_after, inputs
        )
        self._validate_halt_conditions(halt_before, halt_after)
        while self.has_next_action():
            # self.step will only return None if there is no next action, so we can rely on tuple unpacking
            prior_action, result, state = await self.astep(inputs=inputs)
            yield prior_action, result, state
            if self._should_halt_iterate(halt_before, halt_after, prior_action):
                break

    @telemetry.capture_function_usage
    def run(
        self,
        *,
        halt_before: list[str] = None,
        halt_after: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Action, Optional[dict], State]:
        """Runs your application through until completion. Does
        not give access to the state along the way -- if you want that, use iterate().

        :param halt_before: The list of actions to halt before execution of. It will halt on the first one.
        :param halt_after: The list of actions to halt after execution of. It will halt on the first one.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world.
            Note that this is only used for the first iteration -- subsequent iterations will not use this.
        :return: The final state, and the results of running the actions in the order that they were specified.
        """
        gen = self.iterate(halt_before=halt_before, halt_after=halt_after, inputs=inputs)
        while True:
            try:
                next(gen)
            except StopIteration as e:
                return e.value

    @telemetry.capture_function_usage
    async def arun(
        self,
        *,
        halt_before: list[str] = None,
        halt_after: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Action, Optional[dict], State]:
        """Runs your application through until completion, using async. Does
        not give access to the state along the way -- if you want that, use iterate().

        :param halt_before: The list of actions to halt before execution of. It will halt on the first one.
        :param halt_after: The list of actions to halt after execution of. It will halt on the first one.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world
        :return: The final state, and the results of running the actions in the order that they were specified.
        """
        prior_action = None
        result = None
        halt_before, halt_after, inputs = self._clean_iterate_params(
            halt_before, halt_after, inputs
        )
        self._validate_halt_conditions(halt_before, halt_after)
        async for prior_action, result, state in self.aiterate(
            halt_before=halt_before, halt_after=halt_after, inputs=inputs
        ):
            pass
        return self._return_value_iterate(halt_before, halt_after, prior_action, result)

    @telemetry.capture_function_usage
    def stream_result(
        self,
        halt_after: list[str],
        halt_before: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Action, StreamingResultContainer]:
        """Streams a result out.

        :param halt_after: The list of actions to halt after execution of. It will halt on the first one.
        :param halt_before: The list of actions to halt before execution of. It will halt on the first one. Note that
            if this is met, the streaming result container will be empty (and return None) for the result, having an empty generator.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world
        :return: A streaming result container, which is a generator that will yield results as they come in, as well as cache/give you the final result,
            and update state accordingly.

        This is meant to be used with streaming actions -- :py:meth:`streaming_action <burr.core.action.streaming_action>`
        or :py:class:`StreamingAction <burr.core.action.StreamingAction>` It returns a
        :py:class:`StreamingResultContainer <burr.core.action.StreamingResultContainer>`, which has two capabilities:

        1. It is a generator that streams out the intermediate results of the action
        2. It has a ``.get()`` method that returns the final result of the action, and the final state.

        If ``.get()`` is called before the generator is exhausted, it will block until the generator is exhausted.

        While this container is meant to work with streaming actions, it can also be used with non-streaming actions. In this case,
        the generator will be empty, and the ``.get()`` method will return the final result and state.

        The rules for halt_before and halt_after are the same as for :py:meth:`iterate <burr.core.application.Application.iterate>`,
        and :py:meth:`run <burr.core.application.Application.run>`. In this case, `halt_before` will indicate a *non* streaming action,
        which will be empty. Thus ``halt_after`` takes precedence -- if it is met, the streaming result container will contain the result of the
        halt_after condition.

        The :py:class:`StreamingResultContainer <burr.core.action.StreamingResultContainer>` is meant as a convenience -- specifically this allows for
        hooks, callbacks, etc... so you can take the control flow and still have state updated afterwards. Hooks/state update will be called after an exception
        is thrown during streaming, or the stream is completed. Note that it is undefined behavior to attempt to execute another action while a stream is in progress.


        To see how this works, let's take the following action (simplified as a single-node workflow) as an example:

        .. code-block:: python

            @streaming_action(reads=[], writes=['response'])
            def streaming_response(state: State, prompt: str) -> Generator[dict, None, Tuple[dict, State]]:
                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{
                        'role': 'user',
                        'content': prompt
                        }],
                    temperature=0,
                )
                buffer = []
                for chunk in response:
                    delta = chunk.choices[0].delta.content
                    buffer.append(delta)
                    # yield partial results
                    yield {'response': delta}, None # indicate that we are not done by returning a `None` state!
                full_response = ''.join(buffer)
                # return the final result
                yield {'response': full_response}, state.update(response=full_response)

        To use streaming_result, you pass in names of streaming actions (such as the one above) to the halt_after
        parameter:

        .. code-block:: python

            application = ApplicationBuilder().with_actions(streaming_response=streaming_response)...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = application.stream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            for result in streaming_result:
                print(result['response']) # one by one

            result, state = streaming_result.get()
            print(result) #  all at once

        Note that if you have multiple halt_after conditions, you can use the ``.action`` attribute to get the action that
        was run.

        .. code-block:: python

            application = ApplicationBuilder().with_actions(
                streaming_response=streaming_response,
                error=error # another function that outputs an error, streaming
            )...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = application.stream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            color = "red" if action.name == "error" else "green"
            for result in streaming_result:
                print(format(result['response'], color)) # assumes that error and streaming_response both have the same output shape

        .. code-block:: python

            application = ApplicationBuilder().with_actions(
                streaming_response=streaming_response,
                error=non_streaming_error # a non-streaming function that outputs an error
            )...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = application.stream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            color = "red" if action.name == "error" else "green"
            if action.name == "streaming_response": # can also use the ``.streaming`` attribute of action
                for result in output:
                     print(format(result['response'], color)) # assumes that error and streaming_response both have the same output shape
            else:
                result, state = output.get()
                print(format(result['response'], color))
        """
        halt_before, halt_after, inputs = self._clean_iterate_params(
            halt_before, halt_after, inputs
        )
        self._validate_halt_conditions(halt_before, halt_after)
        next_action = self.get_next_action()
        if next_action is None:
            raise ValueError(
                f"Cannot stream result -- no next action found! Prior action was: {self._state[PRIOR_STEP]}"
            )
        if next_action.name not in halt_after:
            # fast forward until we get to the action
            # run already handles incrementing sequence IDs, nothing to worry about here
            next_action, results, state = self.run(
                halt_before=halt_after + halt_before, inputs=inputs
            )
            # In this case, we are ready to halt and return an empty generator
            # The results will be None, and the state will be the final state
            # For context, this is specifically for the case in which you want to have
            # multiple terminal points with a unified API, where some are streaming, and some are not.
            if next_action.name in halt_before and next_action.name not in halt_after:
                return next_action, StreamingResultContainer.pass_through(
                    results=results, final_state=state
                )
        self._increment_sequence_id()
        self._adapter_set.call_all_lifecycle_hooks_sync(
            "pre_run_step",
            action=next_action,
            state=self._state,
            inputs=inputs,
            sequence_id=self.sequence_id,
            app_id=self._uid,
            partition_key=self._partition_key,
        )

        # we need to track if there's any exceptions that occur during this
        try:

            def process_result(result: dict, state: State) -> Tuple[Dict[str, Any], State]:
                new_state = self._update_internal_state_value(state, next_action)
                self._set_state(new_state)
                return result, new_state

            def callback(
                result: Optional[dict],
                state: State,
                exc: Optional[Exception] = None,
            ):
                self._adapter_set.call_all_lifecycle_hooks_sync(
                    "post_run_step",
                    app_id=self._uid,
                    partition_key=self._partition_key,
                    action=next_action,
                    state=state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=exc,
                )

            action_inputs = self._process_inputs(inputs, next_action)
            if not next_action.streaming:
                # In this case we are halting at a non-streaming condition
                # This is allowed as we want to maintain a more consistent API
                action, result, state = self._step(inputs=inputs, _run_hooks=False)
                self._adapter_set.call_all_lifecycle_hooks_sync(
                    "post_run_step",
                    app_id=self._uid,
                    partition_key=self._partition_key,
                    action=next_action,
                    state=self._state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=None,
                )
                return action, StreamingResultContainer.pass_through(
                    results=result, final_state=state
                )
            if next_action.single_step:
                next_action = cast(SingleStepStreamingAction, next_action)
                generator = _run_single_step_streaming_action(
                    next_action, self._state, action_inputs
                )
                return next_action, StreamingResultContainer(
                    generator, self._state, process_result, callback
                )
            else:
                next_action = cast(StreamingAction, next_action)
                generator = _run_multi_step_streaming_action(
                    next_action, self._state, action_inputs
                )
        except Exception as e:
            # We only want to raise this in the case of an exception
            # otherwise, this will get delegated to the finally
            # block of the streaming result container
            self._adapter_set.call_all_lifecycle_hooks_sync(
                "post_run_step",
                app_id=self._uid,
                partition_key=self._partition_key,
                action=next_action,
                state=self._state,
                result=None,
                sequence_id=self.sequence_id,
                exception=e,
            )
            raise
        return next_action, StreamingResultContainer(
            generator, self._state, process_result, callback
        )

    @telemetry.capture_function_usage
    async def astream_result(
        self,
        halt_after: list[str],
        halt_before: list[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Action, AsyncStreamingResultContainer]:
        """Streams a result out in an asynchronous manner.

        :param halt_after: The list of actions to halt after execution of. It will halt on the first one.
        :param halt_before: The list of actions to halt before execution of. It will halt on the first one. Note that
            if this is met, the streaming result container will be empty (and return None) for the result, having an empty generator.
        :param inputs: Inputs to the action -- this is if this action requires an input that is passed in from the outside world
        :return: An asynchronous :py:class:`AsyncStreamingResultContainer <burr.core.action.AsyncStreamingResultContainer>`, which is a generator that will yield results as they come in, as well as cache/give you the final result,
            and update state accordingly.

        This is meant to be used with streaming actions -- :py:meth:`streaming_action <burr.core.action.streaming_action>`
        or :py:class:`StreamingAction <burr.core.action.StreamingAction>` It returns a
        :py:class:`StreamingResultContainer <burr.core.action.StreamingResultContainer>`, which has two capabilities:

        1. It is a generator that streams out the intermediate results of the action
        2. It has an async ``.get()`` method that returns the final result of the action, and the final state.

        If ``.get()`` is called before the generator is exhausted, it will block until the generator is exhausted.

        While this container is meant to work with streaming actions, it can also be used with non-streaming actions. In this case,
        the generator will be empty, and the ``.get()`` method will return the final result and state.

        The rules for halt_before and halt_after are the same as for :py:meth:`iterate <burr.core.application.Application.iterate>`,
        and :py:meth:`run <burr.core.application.Application.run>`. In this case, `halt_before` will indicate a *non* streaming action,
        which will be empty. Thus ``halt_after`` takes precedence -- if it is met, the streaming result container will contain the result of the
        halt_after condition.

        The :py:class:`AsyncStreamingResultContainer <burr.core.action.StreamingResultContainer>` is meant as a convenience -- specifically this allows for
        hooks, callbacks, etc... so you can take the control flow and still have state updated afterwards. Hooks/state update will be called after an exception
        is thrown during streaming, or the stream is completed. Note that it is undefined behavior to attempt to execute another action while a stream is in progress.


        To see how this works, let's take the following action (simplified as a single-node workflow) as an example:

        .. code-block:: python

            client = openai.AsyncClient()

            @streaming_action(reads=[], writes=['response'])
            async def streaming_response(state: State, prompt: str) -> Generator[dict, None, Tuple[dict, State]]:
                response = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[{
                        'role': 'user',
                        'content': prompt
                        }],
                    temperature=0,
                )
                buffer = []
                async for chunk in response: # use an async for loop
                    delta = chunk.choices[0].delta.content
                    buffer.append(delta)
                    # yield partial results
                    yield {'response': delta}, None # indicate that we are not done by returning a `None` state!
                # make sure to join with the buffer!
                full_response = ''.join(buffer)
                # yield the final result at the end + the state update
                yield {'response': full_response}, state.update(response=full_response)

        To use streaming_result, you pass in names of streaming actions (such as the one above) to the halt_after
        parameter:

        .. code-block:: python

            application = ApplicationBuilder().with_actions(streaming_response=streaming_response)...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = application.astream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            async for result in streaming_result:
                print(result['response']) # one by one

            result, state = await streaming_result.get()
            print(result['response']) #  all at once

        Note that if you have multiple halt_after conditions, you can use the ``.action`` attribute to get the action that
        was run.

        .. code-block:: python

            application = ApplicationBuilder().with_actions(
                streaming_response=streaming_response,
                error=error # another function that outputs an error, streaming
            )...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = await application.astream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            color = "red" if action.name == "error" else "green"
            for result in streaming_result:
                print(format(result['response'], color)) # assumes that error and streaming_response both have the same output shape

        .. code-block:: python

            application = ApplicationBuilder().with_actions(
                streaming_response=streaming_response,
                error=non_streaming_error # a non-streaming function that outputs an error
            )...build()
            prompt = "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ..."
            action, streaming_result = await application.astream_result(halt_after='streaming_response', inputs={"prompt": prompt})
            color = "red" if action.name == "error" else "green"
            if action.name == "streaming_response": # can also use the ``.streaming`` attribute of action
                async for result in streaming_result:
                     print(format(result['response'], color)) # assumes that error and streaming_response both have the same output shape
            else:
                result, state = await output.get()
                print(format(result['response'], color))
        """
        halt_before, halt_after, inputs = self._clean_iterate_params(
            halt_before, halt_after, inputs
        )
        self._validate_halt_conditions(halt_before, halt_after)
        next_action = self.get_next_action()
        if next_action is None:
            raise ValueError(
                f"Cannot stream result -- no next action found! Prior action was: {self._state[PRIOR_STEP]}"
            )
        if next_action.name not in halt_after:
            # fast forward until we get to the action
            # run already handles incrementing sequence IDs, nothing to worry about here
            next_action, results, state = await self.arun(
                halt_before=halt_after + halt_before, inputs=inputs
            )
            # In this case, we are ready to halt and return an empty generator
            # The results will be None, and the state will be the final state
            # For context, this is specifically for the case in which you want to have
            # multiple terminal points with a unified API, where some are streaming, and some are not.
            if next_action.name in halt_before and next_action.name not in halt_after:
                return next_action, AsyncStreamingResultContainer.pass_through(
                    results=results, final_state=state
                )
        self._increment_sequence_id()
        await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
            "pre_run_step",
            action=next_action,
            state=self._state,
            inputs=inputs,
            sequence_id=self.sequence_id,
            app_id=self._uid,
            partition_key=self._partition_key,
        )
        try:

            def process_result(result: dict, state: State) -> Tuple[Dict[str, Any], State]:
                new_state = self._update_internal_state_value(state, next_action)
                self._set_state(new_state)
                return result, new_state

            async def callback(
                result: Optional[dict],
                state: State,
                exc: Optional[Exception] = None,
            ):
                await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
                    "post_run_step",
                    app_id=self._uid,
                    partition_key=self._partition_key,
                    action=next_action,
                    state=state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=exc,
                )

            action_inputs = self._process_inputs(inputs, next_action)
            if not next_action.streaming:
                # In this case we are halting at a non-streaming condition
                # This is allowed as we want to maintain a more consistent API
                # TODO -- get this to work with async. Figure out how to run the async step...
                action, result, state = await self._astep(inputs=inputs, _run_hooks=False)
                await self._adapter_set.call_all_lifecycle_hooks_sync_and_async(
                    "post_run_step",
                    app_id=self._uid,
                    partition_key=self._partition_key,
                    action=next_action,
                    state=self._state,
                    result=result,
                    sequence_id=self.sequence_id,
                    exception=None,
                )
                return action, AsyncStreamingResultContainer.pass_through(
                    results=result, final_state=state
                )
            if next_action.single_step:
                next_action = cast(SingleStepStreamingAction, next_action)
                if not next_action.is_async():
                    raise ValueError(
                        f"Action: {next_action.name} is not"
                        "an async action, but is marked as streaming. "
                        "Currently we do not support running synchronous "
                        "streaming actions with astream_result, although we plan to in the future. "
                        "For now, convert the action to async. Please open up an issue if you hit this. "
                    )
                generator = _arun_single_step_streaming_action(
                    next_action, self._state, action_inputs
                )
                return next_action, AsyncStreamingResultContainer(
                    generator, self._state, process_result, callback
                )
            else:
                if not next_action.is_async():
                    raise ValueError(
                        f"Action: {next_action.name} is not"
                        "an async action, but is marked as streaming. "
                        "Currently we do not support running synchronous "
                        "streaming actions with astream_result, although we plan to in the future. "
                        "For now, convert the action to async. Please open up an issue if you hit this. "
                    )
                next_action = cast(AsyncStreamingAction, next_action)
                generator = _arun_multi_step_streaming_action(
                    next_action, self._state, action_inputs
                )
        except Exception as e:
            # We only want to raise this in the case of an exception
            # otherwise, this will get delegated to the finally
            # block of the streaming result container
            self._adapter_set.call_all_lifecycle_hooks_sync(
                "post_run_step",
                app_id=self._uid,
                partition_key=self._partition_key,
                action=next_action,
                state=self._state,
                result=None,
                sequence_id=self.sequence_id,
                exception=e,
            )
            raise
        return next_action, AsyncStreamingResultContainer(
            generator, self._state, process_result, callback
        )

    @telemetry.capture_function_usage
    def visualize(
        self,
        output_file_path: Optional[str] = None,
        include_conditions: bool = False,
        include_state: bool = False,
        view: bool = False,
        engine: Literal["graphviz"] = "graphviz",
        **engine_kwargs: Any,
    ) -> Optional["graphviz.Digraph"]:  # noqa: F821
        """Visualizes the application graph using graphviz. This will render the graph.

        :param output_file_path: The path to save this to, None if you don't want to save. Do not pass an extension
            for graphviz, instead pass `format` in `engine_kwargs` (e.g. `format="png"`)
        :param include_conditions: Whether to include condition strings on the edges (this can get noisy)
        :param include_state: Whether to indicate the action "signature" (reads/writes) on the nodes
        :param view: Whether to bring up a view
        :param engine: The engine to use -- only graphviz is supported for now
        :param engine_kwargs: Additional kwargs to pass to the engine
        :return: The graphviz object
        """
        if engine != "graphviz":
            raise ValueError(f"Only graphviz is supported for now, not {engine}")
        try:
            import graphviz  # noqa: F401
        except ModuleNotFoundError:
            logger.exception(
                " graphviz is required for visualizing the application graph. Install it with:"
                '\n\n  pip install "burr[graphviz]" or pip install graphviz \n\n'
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
        for g_key, g_value in engine_kwargs.items():
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
            required_inputs, optional_inputs = action.optional_and_required_inputs
            for input_ in required_inputs | optional_inputs:
                if input_.startswith("__"):
                    # These are internally injected by the framework
                    continue
                input_name = f"input__{input_}"
                digraph.node(input_name, shape="oval", style="dashed", label=f"input: {input_}")
                digraph.edge(input_name, action.name)
        for transition in self._transitions:
            condition = transition.condition
            digraph.edge(
                transition.from_.name,
                transition.to.name,
                label=condition.name if include_conditions and condition is not default else None,
                style="dashed" if transition.condition is not default else "solid",
            )
        if output_file_path:
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
    def parent_pointer(self) -> Optional[burr_types.ParentPointer]:
        """Gives the parent pointer of an application (from where it was forked).
        This is None if it was not forked.

        :return: The parent pointer object.
        """
        return self._parent_pointer

    def _create_graph(self) -> ApplicationGraph:
        """Internal-facing utility function for creating an ApplicationGraph"""
        all_actions = {action.name: action for action in self._actions}
        return ApplicationGraph(
            actions=self._actions,
            transitions=self._transitions,
            entrypoint=all_actions[self._initial_step],
        )

    @property
    def graph(self) -> ApplicationGraph:
        """Application graph object -- if you want to inspect, visualize, etc..
        this is what you want.

        :return: The application graph object
        """
        return self._graph

    @property
    def sequence_id(self) -> Optional[int]:
        """gives the sequence ID of the current (next) action.
        This is incremented prior to every step. Any logging, etc... will use the current
        step's sequence ID

        :return: The sequence ID of the current (next) action
        """
        return self._state.get(SEQUENCE_ID)

    def _increment_sequence_id(self):
        if SEQUENCE_ID not in self._state:
            self._state = self._state.update(**{SEQUENCE_ID: 0})
        else:
            self._state = self._state.update(**{SEQUENCE_ID: self.sequence_id + 1})

    def _set_sequence_id(self, sequence_id: int):
        self._state = self._state.update(**{SEQUENCE_ID: sequence_id})

    @property
    def uid(self) -> str:
        """Unique ID for the application. This must be unique across *all* applications in a search space.
        This is used by persistence/tracking to ensure that applications have meanings.

        Every application has this -- if not assigned, it will be randomly generated.

        :return: The unique ID for the application
        """
        return self._uid

    @property
    def partition_key(self) -> Optional[str]:
        """Partition key for the application. This is designed to add semantic meaning to
        the application, and be leveraged by persistence systems to select/find applications.

        Note this is optional -- if it is not included, you will need to use a persister that
        supports a null partition key.

        :return: The partition key, None if not set
        """
        return self._partition_key

    @property
    def builder(self) -> Optional["ApplicationBuilder"]:
        """Returns the application builder that was used to build this application.
        Note that this asusmes the application was built using the builder. Otherwise,

        :return: The application builder
        """
        return self._builder


def _assert_set(value: Optional[Any], field: str, method: str):
    if value is None:
        raise ValueError(
            ERROR_MESSAGE
            + f"Must set `{field}` before building application! Do so with ApplicationBuilder.{method}"
        )


def _validate_transitions(
    transitions: Optional[List[Tuple[str, str, Condition]]], actions: Set[str]
):
    _assert_set(transitions, "_transitions", "with_transitions")
    exhausted = {}  # items for which we have seen a default transition
    for from_, to, condition in transitions:
        if from_ not in actions:
            raise ValueError(
                f"Transition source: `{from_}` not found in actions! "
                f"Please add to actions using with_actions({from_}=...)"
            )
        if to not in actions:
            raise ValueError(
                f"Transition target: `{to}` not found in actions! "
                f"Please add to actions using with_actions({to}=...)"
            )
        if condition.name == "default":  # we have seen a default transition
            if from_ in exhausted:
                raise ValueError(
                    f"Transition `{from_}` -> `{to}` is redundant -- "
                    f"a default transition has already been set for `{from_}`"
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


def _validate_app_id(app_id: Optional[str]):
    if app_id is None:
        raise ValueError(
            "App ID was None. Please ensure that you set an app ID using with_identifiers(app_id=...), or default"
            "not setting it and letting the system generate one for you."
        )


def _validate_actions(actions: Optional[List[Action]]):
    _assert_set(actions, "_actions", "with_actions")
    if len(actions) == 0:
        raise ValueError("Must have at least one action in the application!")


class ApplicationBuilder:
    def __init__(self):
        self.state: Optional[State] = None
        self.transitions: Optional[List[Tuple[str, str, Condition]]] = None
        self.actions: Optional[List[Action]] = None
        self.start: Optional[str] = None
        self.lifecycle_adapters: List[LifecycleAdapter] = list()
        self.app_id: str = str(uuid.uuid4())
        self.partition_key: Optional[str] = None
        self.sequence_id: Optional[int] = None
        self.initializer = None
        self.use_entrypoint_from_save_state: Optional[bool] = None
        self.default_state: Optional[dict] = None
        self.fork_from_app_id: Optional[str] = None
        self.fork_from_partition_key: Optional[str] = None
        self.fork_from_sequence_id: Optional[int] = None
        self.loaded_from_fork: bool = False

    def with_identifiers(
        self, app_id: str = None, partition_key: str = None, sequence_id: int = None
    ) -> "ApplicationBuilder":
        """Assigns various identifiers to the application. This is used for tracking, persistence, etc...

        :param app_id: Application ID -- this will be assigned to a uuid if not set.
        :param partition_key: Partition key -- this is used for disambiguating groups of applications. For instance, a unique user ID, etc...
            This is coupled to persistence, and is used to query for/select application runs.
        :param sequence_id: Sequence ID that we want this to start at. If you're using ``.initialize``, this will be set. Otherwise this is
            solely for resetting/starting at a specified position.
        :return: The application builder for future chaining.
        """
        if app_id is not None:
            self.app_id = app_id
        if partition_key is not None:
            self.partition_key = partition_key
        if sequence_id is not None:
            self.sequence_id = sequence_id
        return self

    def with_state(self, **kwargs) -> "ApplicationBuilder":
        """Sets initial values in the state. If you want to load from a prior state,
        you can do so here and pass the values in.

        TODO -- enable passing in a `state` object instead of `**kwargs`

        :param kwargs: Key-value pairs to set in the state
        :return: The application builder for future chaining.
        """
        if self.initializer is not None:
            raise ValueError(
                ERROR_MESSAGE + "You cannot set state if you are loading state"
                "the .initialize_from() API. Either allow the persister to set the "
                "state, or set the state manually."
            )
        if self.state is not None:
            self.state = self.state.update(**kwargs)
        else:
            self.state = State(kwargs)
        return self

    def with_entrypoint(self, action: str) -> "ApplicationBuilder":
        """Adds an entrypoint to the application. This is the action that will be run first.
        This can only be called once.

        :param action: The name of the action to set as the entrypoint
        :return: The application builder for future chaining.
        """
        # TODO -- validate only called once
        if self.start is not None:
            raise ValueError(
                ERROR_MESSAGE
                + "You cannot set the entrypoint if you are loading a persister using "
                "the .initialize_from() API. Either allow the persister to set the "
                "entrypoint/provide a default, or set the entrypoint + state manually."
            )
        self.start = action
        return self

    def with_actions(
        self, *action_list: Union[Action, Callable], **action_dict: Union[Action, Callable]
    ) -> "ApplicationBuilder":
        """Adds an action to the application. The actions are granted names (using the with_name)
        method post-adding, using the kw argument. If it already has a name (or you wish to use the function name, raw, and
        it is a function-based-action), then you can use the *args* parameter. This is the only supported way to add actions.

        :param action_list: Actions to add -- these must have a name or be function-based (in which case we will use the function-name)
        :param action_dict: Actions to add, keyed by name
        :return: The application builder for future chaining.
        """
        if self.actions is None:
            self.actions = []
        for action_value in action_list:
            if inspect.isfunction(action_value):
                self.actions.append(create_action(action_value, action_value.__name__))
            elif isinstance(action_value, Action):
                if not action_value.name:
                    raise ValueError(
                        ERROR_MESSAGE + f"Action: {action_value} must have a name set. "
                        "If you hit this, you should probably be using the "
                        "**kwargs parameter (or call with_name(your_name) on the action)."
                    )
                self.actions.append(action_value)
        for key, value in action_dict.items():
            self.actions.append(create_action(value, key))
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

        :param adapters: Adapter to add
        :return: The application builder for future chaining.
        """
        self.lifecycle_adapters.extend(adapters)
        return self

    def with_tracker(
        self,
        tracker: Union[
            Literal["local"], LifecycleAdapter
        ] = "local",  # TODO -- tighten type-check for tracker. For now it has the lifecycle adapter
        project: str = "default",
        params: Dict[str, Any] = None,
    ):
        """Adds a "tracker" to the application. The tracker specifies
        a project name (used for disambiguating groups of tracers), and plugs into the
        Burr UI. This can either be:

        1. A string (the only supported one right now is "local"), and a set of parameters for a set of supported trackers.
        2. A lifecycle adapter object that does tracking (up to you how to implement it).

        (1) internally creates a :py:class:`LocalTrackingClient <burr.tracking.client.LocalTrackingClient>` object, and adds it to the lifecycle adapters.
        (2) adds the lifecycle adapter to the lifecycle adapters.

        :param tracker: Tracker to use. ``local`` creates one, else pass one in.
        :param project: Project name -- used if the tracker is string-specified (local).
        :param params: Parameters to pass to the tracker if it's string-specified (local).
        :return: The application builder for future chaining.
        """
        # if it's a lifecycle adapter, just add it
        if isinstance(tracker, str):
            if params is None:
                params = {}
            if tracker == "local":
                from burr.tracking.client import LocalTrackingClient

                kwargs = {"project": project}
                kwargs.update(params)
                self.lifecycle_adapters.append(LocalTrackingClient(**kwargs))
            else:
                raise ValueError(f"Tracker {tracker}:{project} not supported")
        else:
            self.lifecycle_adapters.append(tracker)
            if params is not None:
                raise ValueError(
                    "Params are not supported for object-specified trackers, these are already initialized!"
                )
        return self

    def initialize_from(
        self,
        initializer: BaseStateLoader,
        resume_at_next_action: bool,
        default_state: dict,
        default_entrypoint: str,
        fork_from_app_id: str = None,
        fork_from_partition_key: str = None,
        fork_from_sequence_id: int = None,
    ) -> "ApplicationBuilder":
        """Initializes the application we will build from some prior state object.

        Note (1) that you can *either* call this or use `with_state` and `with_entrypoint`.

        Note (2) if you want to continue a prior application and don't want to fork it into a new application ID,
        the values in `.with_identifiers()` will be used to query for prior state.

        :param initializer: The persister object to use for initialization. Likely the same one called with ``with_state_persister``.
        :param resume_at_next_action: Whether to resume at the next action, or default to the ``default_entrypoint``
        :param default_state: The default state to use if it does not exist. This is a dictionary.
        :param default_entrypoint: The default entry point to use if it does not exist or you elect not to resume_at_next_action.
        :param fork_from_app_id: The app ID to fork from, not to be confused with the current app_id that is set with `.with_identifiers()`. This is used to fork from a prior application run.
        :param fork_from_partition_key: The partition key to fork from a prior application. Optional. `fork_from_app_id` required.
        :param fork_from_sequence_id: The sequence ID to fork from a prior application run. Optional, defaults to latest. `fork_from_app_id` required.
        :return: The application builder for future chaining.
        """
        if self.start is not None or self.state is not None:
            raise ValueError(
                ERROR_MESSAGE
                + "Cannot call initialize_from if you have already set state or an entrypoint! "
                "You can either use the initializer *or* set the state and entrypoint manually."
            )
        if not fork_from_app_id and (fork_from_partition_key or fork_from_sequence_id):
            raise ValueError(
                ERROR_MESSAGE
                + "If you set fork_from_partition_key or fork_from_sequence_id, you must also set fork_from_app_id. "
                "See .initialize_from() documentation."
            )
        self.initializer = initializer
        self.resume_at_next_action = resume_at_next_action
        self.default_state = default_state
        self.start = default_entrypoint
        self.fork_from_app_id = fork_from_app_id
        self.fork_from_partition_key = fork_from_partition_key
        self.fork_from_sequence_id = fork_from_sequence_id
        return self

    def with_state_persister(
        self, persister: Union[BaseStateSaver, LifecycleAdapter], on_every: str = "step"
    ) -> "ApplicationBuilder":
        """Adds a state persister to the application. This is a way to persist state out to a database, file, etc...
        at the specified interval. This is one of two options:

        1. [normal mode] A BaseStateSaver object -- this is a utility class that makes it easy to save/load
        2. [power-user-mode] A lifecycle adapter -- this is a custom class that you use to save state.

        The framework will wrap the BaseStateSaver object in a PersisterHook, which is a post-run.

        :param persister: The persister to add
        :param on_every: The interval to persist state. Currently only "step" is supported.
        :return: The application builder for future chaining.
        """
        if on_every != "step":
            raise ValueError(f"on_every {on_every} not supported")
        if not isinstance(persister, persistence.BaseStateSaver):
            self.lifecycle_adapters.append(persister)
        else:
            self.lifecycle_adapters.append(persistence.PersisterHook(persister))
        return self

    def _load_from_persister(self):
        """Loads from the set persister and into this current object.

        Mutates:
         - self.state
         - self.sequence_id
         - maybe self.start

        """
        if self.fork_from_app_id is not None:
            if self.app_id == self.fork_from_app_id:
                raise ValueError(
                    ERROR_MESSAGE + "Cannot fork and save to the same app_id. "
                    "Please update the app_id passed in via with_identifiers(), "
                    "or don't pass in a fork_from_app_id value to `initialize_from()`."
                )
            _partition_key = self.fork_from_partition_key
            _app_id = self.fork_from_app_id
            _sequence_id = self.fork_from_sequence_id
        else:
            # only use the with_identifier values if we're not forking from a previous app
            _partition_key = self.partition_key
            _app_id = self.app_id
            _sequence_id = self.sequence_id
        # load state from persister
        load_result = self.initializer.load(_partition_key, _app_id, _sequence_id)
        if load_result is None:
            if self.fork_from_app_id is not None:
                logger.warning(
                    f"{self.initializer.__class__.__name__} returned None while trying to fork from: "
                    f"partition_key:{_partition_key}, app_id:{_app_id}, "
                    f"sequence_id:{_sequence_id}. "
                    "You explicitly requested to fork from a prior application run, but it does not exist. "
                    "Defaulting to state defaults instead."
                )
            # there was nothing to load -- use default state
            self.state = self.state.update(**self.default_state)
            self.sequence_id = None  # has to start at None
        else:
            self.loaded_from_fork = True
            if load_result["state"] is None:
                raise ValueError(
                    ERROR_MESSAGE
                    + f"Error: {self.initializer.__class__.__name__} returned {load_result} for "
                    f"partition_key:{_partition_key}, app_id:{_app_id}, "
                    f"sequence_id:{_sequence_id}, "
                    "but value for state was None! This is not allowed. Please return just None in this case, "
                    "or double check that persisted state can never be a None value."
                )
            # TODO: capture parent app ID relationship & wire it through
            # there was something
            last_position = load_result["position"]
            self.state = load_result["state"]
            self.sequence_id = load_result["sequence_id"]
            status = load_result["status"]
            if self.resume_at_next_action:
                # if we're supposed to resume where we saved from
                if status == "completed":
                    # completed means we set prior step to current to go to next action
                    self.state = self.state.update(**{PRIOR_STEP: last_position})
                else:
                    # else we failed we just start at that node
                    self.start = last_position
                    self.reset_to_entrypoint()
            else:
                # self.start is already set to the default. We don't need to do anything.
                pass

    def reset_to_entrypoint(self):
        self.state = self.state.wipe(delete=[PRIOR_STEP])

    @telemetry.capture_function_usage
    def build(self) -> Application:
        """Builds the application.

        This function is a bit messy as we iron out the exact logic and rigor we want around things.

        :return: The application object
        """
        _validate_actions(self.actions)
        actions_by_name = {action.name: action for action in self.actions}
        all_actions = set(actions_by_name.keys())
        _validate_transitions(self.transitions, all_actions)
        _validate_app_id(self.app_id)
        if self.state is None:
            self.state = State()
        if self.initializer:
            # sets state, sequence_id, and maybe start
            self._load_from_persister()
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
            uid=self.app_id,
            partition_key=self.partition_key,
            sequence_id=self.sequence_id,
            adapter_set=LifecycleAdapterSet(*self.lifecycle_adapters),
            builder=self,
            parent_pointer=burr_types.ParentPointer(
                app_id=self.fork_from_app_id,
                partition_key=self.fork_from_partition_key,
                sequence_id=self.fork_from_sequence_id,
            )
            if self.loaded_from_fork
            else None,
        )
