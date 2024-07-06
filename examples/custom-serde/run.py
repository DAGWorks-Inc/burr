"""
Example of running the application
from another module to make sure the
SERDE classes are registered in a non __main__
module namespace.

e.g. python run.py
and then
burr-test-case create --project-name serde-example --app-id APP_ID --sequence-id 3 --serde-module application.py
"""
import pprint
import uuid

import application  # noqa
from application import build_application

from burr.core import State

# build
app = build_application("client-123", str(uuid.uuid4()))
app.visualize(
    output_file_path="statemachine", include_conditions=True, include_state=True, format="png"
)
# run
action, result, state = app.run(
    halt_after=["terminal_action"], inputs={"user_input": "hello world"}
)
# serialize
serialized_state = state.serialize()
pprint.pprint(serialized_state)
# deserialize
deserialized_state = State.deserialize(serialized_state)
# assert that the state is the same after serialization and deserialization
assert state.get_all() == deserialized_state.get_all()
