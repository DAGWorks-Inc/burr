================================
SDLC with LLMs
================================
If you're building an LLM-based application, you'll want to follow a slightly different software development lifecycle (SDLC)
than you would for a traditional software project. Here's a rough outline of what that might look like:

.. image:: ../_static/burr_sdlc.png
   :alt: SDLC with LLMs
   :align: center

The two cycles that exist are:

1. App Dev Loop.
2. Test Driven Development Loop.

and you will use one to feed into the other, etc.

Walking through the diagram the SDLC looks like this:

1. Write code with Burr.
2. Use Burr's integrated observability, and trace all parts of your application.
3. With the data collected, you can: (1) annotate what was captured and export it, or (2) create a pytest fixture with it.
4. Create a data set from the annotated data or by running tests.
5. Evaluate the data set.
6. Analyze the results.
7. Either adjust code or prompts, or ship the code.
8. Iterate using one of the loops...
