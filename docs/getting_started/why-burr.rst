=================
Why Burr
=================

---------------------------------------
An abstraction to make your life easier
---------------------------------------

Why do you need a state machine for your applications? Won't the normal programming constructs suffice?

Yes, until a point. Let's look at a chatbot as an example. Here's a simple design of something gpt-like:

#. Accept a prompt from the user
#. Does some simple checks/validations on that prompt (is it safe/within the terms of service)
#. If (2) it then decides the mode to which to respond to that prompt from a set of capabilities. Else respond accordingly:
     *  Generate an image
     *  Answer a question
     *  Write some code
     *  ...
#. It then queries the appropriate model with the prompt, formatted as expected
#. If this fails, we present an error message
#. If this succeeds, we present the response to the user
#. Await a new prompt, GOTO (1)

Visually, we might have an implementation/spec that looks like this:

.. image:: ../_static/demo_graph.png
    :align: center


While this involves multiple API calls, error-handling, etc... it is definitely possible to get a prototype
that looks slick out without too much abstraction. Let's get this to production, however. We need to:

#. Add monitoring to figure out if/why any of our API calls return strange results
#. Understand the decisions made by the application -- E.G. why it chose certain modes, why it formatted a response correctly. This involves:
    * Tracking all the prompts/responses
    * Going back in time to examine the state of the application at a given point
#. Debug it in a local mode, step-by-step, using the state we observed in production
#. Add new capabilities to the application
#. Monitor the performance of the application -- which steps/decisions are taking the longest?
#. Monitor the cost of running the application -- how many tokens are we accepting from/delivering to the user.
#. Save the state out to some external store so you can restart the conversation from where you left off

And this is the tip of the iceberg -- chatbots (and all stateful applications) get really complicated, really quickly.

Burr is designed to unlock the capabilities above and more -- decomposing your application into functions that manipulate state
and transition, with hooks that allow you to customize any part of the application. It is a platform on top of which you can build any of the
production requirements above, and comes with many of them out of the box!
