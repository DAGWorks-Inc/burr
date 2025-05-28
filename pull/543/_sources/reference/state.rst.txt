=================
State
=================

Use the state API to manipulate the state of the application.

.. autoclass:: burr.core.state.State
   :members:

   .. automethod:: __init__


Custom field level serialization and deserialization
----------------------------------------------------
Use the following to register custom field level serialization and deserialization functions.
Note: this registration is global for any state field with the same name.

.. autofunction:: burr.core.state.register_field_serde
