# Creating robust applications by creating test cases
This example shows you how you can easily create (integration) test cases for Burr your project.

With Burr it is easy to foster a test-driven development mindset when developing actions, which are the building blocks of your Burr
application.

## Motivation

With LLMs non-deterministic behavior can impact your application's behavior. It is important to create test cases to
ensure that your application is robust and behaves as expected; it is easy to tweak a prompt and break
a particular use case. This example shows you how you can create test cases
for your project from real traces, since part of the struggle is to create test cases that are representative of the
real-world behavior of your application -- Burr can make this process easier.

## Steps
1. Build your project with Burr.
2. Run your Burr application with tracking/persistence.
3. Find a trace that you want to create a test case for.
4. Note the partition_key, app_id, and sequence_id of the trace.
5. Create a test case using the `burr create-test-case` command passing the partition_key, app_id, and sequence_id as arguments.
6. Iterate on the test case until it is robust and representative of the real-world behavior of your application.
7. Profit.

## Testing Actions
In `test_application.py` you'll find examples tests for a simple action
that is found in `application.py`.
