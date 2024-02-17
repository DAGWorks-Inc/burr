=====
State
=====

.. _state:

The ``State`` class provides the ability to manipulate state for a given action. It is entirely immutable,
meaning that you can only create new states from old ones, not modify them in place.

State manipulation is done through calling methods on the ``State`` class. The most common write are:

.. code-block:: python

    state.update(foo=bar)  # update the state with the key "foo" set to "bar"
    state.append(foo=bar)  # append "bar" to the list at "foo"
    state.wipe(keep=["foo", "bar"])  # remove all keys except "foo" and "bar"
    state.wipe(delete=["foo", "bar"])  # remove "foo" and "bar" from the state

The read operations extend from those in the `Mapping <https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping>`_
interface, but there are a few extra:

.. code-block:: python

    state.subset(["foo", "bar"])  # return a new state with only the keys "foo" and "bar"
    state.get_all()  # return a dictionary with every key/value of the state

When an update action is run, the state is first subsetted to get just the keys that are being read from,
then the action is run, and a new state is written to. This state is merged back into the original state
after the action is complete. Pseudocode:

.. code-block:: python

    current_state = ...
    read_state = current_state.subset(action.reads)
    result = action.run(new_state)
    write_state = current_state.subset(action.writes)
    new_state = action.update(result, new_state)
    current_state = current_state.merge(new_state)

If you're used to thinking about version control, this is a bit like a commit/checkout/merge mechanism.
