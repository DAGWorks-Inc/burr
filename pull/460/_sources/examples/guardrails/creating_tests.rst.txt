====================
Creating Test Cases
====================

With Burr tracking state is part of the framework. This means creating a realistic test case
for an action involves turning a persister or tracker on and then pulling that state out
for a test case. The following example demonstrates how to create a test case
using the `burr-test-case` command.

Note: writing test cases for GenAI projects can be tricky. The same LLM API calls
can result in different outputs. This means that 'exact' equality tests may not work,
and you'll need to resort to more fuzzy tests like checking for the presence of certain
words or phrases, or using LLMs to grade the output, etc. We aren't opinionated on how you
do this, but in any case, you'll need to write a test case to exercise things, and this
is what we're showing you how to do here.

Test Case Creation Example
--------------------------
Video walkthrough:

.. raw:: html

    <div>
      <iframe width="800" height="455" src="https://www.youtube.com/embed/9U_CMsh0VBI?si=Z-powULn_RO2-2pB" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </div>


Steps:

1. You have built some part of your Burr application.
2. You have found some state you want to test / iterate on.
3. Note the project name, partition key, app id, and sequence id for the state you want to test.
   See orange lines indicating what to pull from the UI in the image below.

    .. image:: _creating_tests.png
       :alt: What you need to pull from the UI for running the command.
       :align: center

4. Run the following command & cut and paste the test to a test file. This will create a `pytest` test.
5. Adjust the test as needed, e.g. what you're validating or asserting and how.

.. code-block:: bash

    burr-test-case create  \
      --project-name "SOME_NAME" \
      --partition-key "SOME_KEY" \
      --app-id "SOME_ID" \
      --sequence-id 0 \
      --target-file-name /tmp/test-case.json

See `github repository example <https://github.com/DAGWorks-Inc/burr/tree/main/examples/test-case-creation>`_
for an example.

Note (1): if you have custom serialization/deserialization logic, you will want to pass in `--serde-module` to the
test case with the module name of your serialization logic.

Note (2): you can pass in `--action-name` to override the action name in the test case. This is useful if you want
to use the output of one action as the input to another action; there are corner cases where this is useful.

Future Work
-----------
We see many more improvements here:

1. Annotating data in the UI to make it easier to pull out.
2. Automatically suggesting tests cases for you to add.
3. Data export / integration with evaluation tools.
4. etc. Please let us know what you need!
