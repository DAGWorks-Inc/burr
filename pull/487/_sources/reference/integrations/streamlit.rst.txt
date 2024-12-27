=======================
Streamlit
=======================

Full Streamlit integration. Tough-points are utility functions.
It is likely this will adapt/change over time, so it is only recommended to use this for debugging/developing.

Install with pypi:

.. code-block:: bash

   pip install burr[streamlit]

.. autoclass:: burr.integrations.streamlit.AppState
    :members:

.. autofunction:: burr.integrations.streamlit.load_state_from_log_file

.. autofunction:: burr.integrations.streamlit.get_state

.. autofunction:: burr.integrations.streamlit.update_state

.. autofunction:: burr.integrations.streamlit.render_state_machine

.. autofunction:: burr.integrations.streamlit.render_action

.. autofunction:: burr.integrations.streamlit.render_state_results

.. autofunction:: burr.integrations.streamlit.set_slider_to_current

.. autofunction:: burr.integrations.streamlit.render_explorer
