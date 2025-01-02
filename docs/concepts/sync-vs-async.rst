===========================
Sync vs Async Applications
===========================

TL;DR
------
1. For applications with horizontal scaling: multiple users, lots of i/o throughput,... go with async. Check out:

   * :py:meth:`.abuild() <.ApplicationBuilder.abuild()>`
   * :py:meth:`.aiterate() <.Application.aiterate()>`
   * :py:meth:`.arun() <.Application.arun()>`
   * :py:meth:`.astream_result() <.Application.astream_result()>`

2. For prototyping applications or high stakes operations,... go with sync.Check out:

   * :py:meth:`.build() <.ApplicationBuilder.build()>`
   * :py:meth:`.iterate() <.Application.iterate()>`
   * :py:meth:`.run() <.Application.run()>`
   * :py:meth:`.stream_result() <.Application.stream_result()>`


Burr does both sync and async
------------------------------
Bellow we give a short breakdown when to consider each case.

In general, Burr is equipped to handle both synchronous and asynchronous runs. We usually do that by
providing both methods (see specific references for more detail and reach out if you feel like we
are missing a specific implementation).

We hope the switch from one to another is as convenient as possible; you only need to substitute
functions/adapters/method calls.

We highly encourage to make a decision to either commit fully to sync or async. Having said that,
there are cases where a hybrid situation may be desirable or unavoidable (testing, prototyping,
legacy code, ...) and we give some options to handle that. The table bellow shows the
possibilities Burr now supports.


.. table:: Cases Burr supports
    :widths: auto

    +------------------------------------------------+----------+----------------------------------+
    | Cases                                          | Works?   | Comment                          |
    +================================================+==========+==================================+
    | Sync Hooks <> Sync Builder <> Sync App Run     |  ✅      | This is a standard use           |
    |                                                |          | case highlighted                 |
    |                                                |          | in sync applications             |
    +------------------------------------------------+----------+----------------------------------+
    | Sync Hooks <> Sync Builder <> Async App Run    |  ⚠️      | This will work for now, but it is|
    |                                                |          | not recommended because there    |
    |                                                |          | will be blocking functions       |
    +------------------------------------------------+----------+----------------------------------+
    | Async Hooks <> Sync Builder <> Sync App Run    |  ⚠️      | This will run (if the async hook |
    |                                                |          | is not a persister), but the     |
    |                                                |          | async hooks are ignored -- will  |
    |                                                |          | be deprecated                    |
    +------------------------------------------------+----------+----------------------------------+
    | Async Hooks <> Sync Builder <> Async App Run   |  ⚠️      | This will run (if the async hook |
    |                                                |          | is not a persister), but you     |
    |                                                |          | should really use the async      |
    |                                                |          | builder                          |
    +------------------------------------------------+----------+----------------------------------+
    | Async Hooks <> Async Builder <> Async App Run  |  ✅      | This is a standard use case      |
    |                                                |          | highlighted       in async       |
    |                                                |          | applications                     |
    +------------------------------------------------+----------+----------------------------------+
    | Async Hooks <> Async Builder <> Sync App Run   |  ❌      | Use async run methods            |
    +------------------------------------------------+----------+----------------------------------+
    | Sync Hooks <> Async Builder <> Sync App Run    |  ❌      | Use sync builder                 |
    +------------------------------------------------+----------+----------------------------------+
    | Sync Hooks <> Async Builder <> Async App Run   |  ⚠️      | This will run (if the sync hook  |
    |                                                |          | is not a persister), but you     |
    |                                                |          | should really use the sync       |
    |                                                |          | builder                          |
    +------------------------------------------------+----------+----------------------------------+


Synchronous Applications
--------------------------
A synchronous application processes tasks sequentially, where the user or calling system must wait for
the agent to finish a task before proceeding.

Advantages
~~~~~~~~~~~~

1. Simplicity:
    * Easier to design and implement as the logic flows linearly.
    * Debugging and maintenance are more straightforward.
2. Deterministic Behavior:
    * Results are predictable and occur in a defined sequence.
    * Ideal for workflows where steps must be completed in strict order.
3. Low Overhead:
    * Useful for tasks that don’t require extensive multitasking or background processing.
    * Rapid prototyping.


Use Cases
~~~~~~~~~~~

1. Short, straightforward tasks:
    * For example, fetching a single database entry or making a quick calculation.
2. High-stakes operations:
    * When the process must proceed step-by-step without the risk of race conditions or overlapping tasks.
3. Interactive applications:
    * Situations where the user must receive immediate feedback before taking the next step, like form validations.

Asynchronous Application
--------------------------
An asynchronous application can perform tasks in parallel or handle multiple requests without waiting for
one to finish before starting another.

Advantages
~~~~~~~~~~~~

1. Efficiency:
    * Makes better use of system resources by handling multiple tasks simultaneously.
    * Reduces idle time, especially when dealing with I/O-bound or network-bound operations.
2. Scalability:
    * Handles large volumes of concurrent tasks more effectively.
    * Useful in systems requiring high throughput, like web servers or chatbots.
3. Non-blocking Execution:
    * Allows other operations to continue while waiting for longer processes to complete.
    * Provides a smoother experience in real-time systems.


Use Cases
~~~~~~~~~~~~

1. Long-running processes:
    * Training machine learning models.
    * Data processing pipelines.
2. I/O-bound tasks:
    * Calling APIs.
    * Retrieving data from remote servers or databases.
3. High-concurrency systems:
    * Chatbots serving multiple users.
    * Customer support systems.
4. Background processing:
    * Notifications, logs, and analytics tasks running while the main application continues.
