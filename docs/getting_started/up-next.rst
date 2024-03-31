=================
Next Steps
=================

You've written your own burr application in a few lines of code. Nice work! Let's look at some less trivial examples.
All of the following are pre-populated in the UI under ``projects/``. You can start the UI by running:

.. code-block:: bash

    burr

Telemetry UI chatbot demo ``demo:chatbot``
------------------------------------------

You'll need the env variable ``OPENAI_API_KEY`` set to your api key for this to work. If you don't
have one, you'll still be able to run it and explore, you just won't be able to chat.

If you haven't already:

.. code-block:: bash

    pip install burr[start]

Then:

.. code-block:: bash

    burr-demo

If you've run ``burr`` and have it open on port 7241, just navigate to `demos/chatbot <http://localhost:7241/demos/chatbot>`_.

Repository Examples
-------------------

For the next examples you'll need the repository cloned:

.. code-block:: bash

    git clone https://github.com/dagworks-inc/burr && cd burr

-------------------------------
Simple Counter ``demo:counter``
-------------------------------

.. code-block:: bash

    cd examples/hello-world-counter
    python application.py

-------------------------------------------
Interactive RAG ``demo:conversational-rag``
-------------------------------------------

This is a toy interactive RAG example. You'll ask questions in the terminal about information it already has...

.. code-block:: bash

    cd examples/conversational-rag
    pip install -r requirements.txt
    python application.py


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
