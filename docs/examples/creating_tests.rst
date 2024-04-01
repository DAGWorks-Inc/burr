====================
Creating Test Cases
====================

With Burr tracking state is part of the framework. This means creating a realistic test case
for an action involves turning a persister or tracker on and then pulling that state out
for a test case. The following example demonstrates how to create a test case
using the `burr-test-case` command.

Test Case Creation Example
--------------------------
Prerequisite:

1. You have built some part of your Burr application.
2. You have found some state you want to test / iterate on.
3. Note the project name, partition key, app id, and sequence id for the state you want to test.
4. Run the following command & cut and paste the test to a test file. This will create a `pytest` test.

```bash
%%sh
burr-test-case create  \
  --project-name "SOME_NAME" \
  --partition-key "SOME_KEY" \
  --app-id "SOME_ID" \
  --sequence-id 0 \
  --target-file-name /tmp/test-case.json
```

See `github repository example <https://github.com/DAGWorks-Inc/burr/tree/main/examples/test-case-creation>`_
for an example.
