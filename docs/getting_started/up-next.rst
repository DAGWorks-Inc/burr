=================
Next Steps
=================

You've written your own burr application in a few lines of code. Nice work! Let's look at some more powerful examples.
Note you'll need the repository cloned to run these -- you can also explore the results without running them in the UI -- it is pre
populated with sample runs.

----------
More demos
----------

Streamlit chatbot ``demo:chatbot``
------------------------------------

You'll need the env variable ``OPENAI_API_KEY`` set to your api key for this to work.

We recommend you keep the app (terminal or streamlit) open in one window while
watching the tracker in the other window. You'll see some interesting things!

.. code-block:: bash

    cd examples/gpt
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Simple Counter ``demo:counter``
-------------------------------

This is just a single terminal command:

.. code-block:: bash

    cd examples/counter
    python application.py

Interactive RAG ``demo:conversational-rag``
-------------------------------------------

This is a toy interactive RAG example. You'll ask questions in the terminal about information it already has...

.. code-block:: bash

    cd examples/conversational_rag
    pip install -r requirements.txt
    python application.py

----------------------
Understanding Concepts
----------------------

If you're more comfortable learning through concepts start here.

Once you're comfortable with the UI, you may want to get a sense of a few of the capabilities
of the Burr library and where you can go to learn more about them:

- :ref:`Creating custom actions <actions>` and calling out to integrated frameworks
- :ref:`Running applications <applications>`, managing their lifeycyle, and inspecting the results
- :ref:`Managing state <state>` -- persisting, inspecting, and updating
- :ref:`Handling transition between nodes <transitions>` and managing the flow of your application
- :ref:`Adding hooks to customize execution <hooks>` and integrate with other systems
