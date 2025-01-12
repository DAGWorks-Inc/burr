===========================
Sync vs Async Applications
===========================

TL;DR
------

Burr supports synchronous (standard python) and asynchronous (``async def``/``await``) applications. At a high leveL:

1. Use the `async` interfaces when you have I/O-heavy applications that require horizontal scaling, and have avaialble asynchronous APIs (E.G. async LLM APIs)

   * :py:meth:`.abuild() <.ApplicationBuilder.abuild()>`
   * :py:meth:`.aiterate() <.Application.aiterate()>`
   * :py:meth:`.arun() <.Application.arun()>`
   * :py:meth:`.astream_result() <.Application.astream_result()>`

2. Use the synchronous interfaces otherwise -- when you have high CPU-bound applications (running models locally), or do not have async APIs to use:

   * :py:meth:`.build() <.ApplicationBuilder.build()>`
   * :py:meth:`.iterate() <.Application.iterate()>`
   * :py:meth:`.run() <.Application.run()>`
   * :py:meth:`.stream_result() <.Application.stream_result()>`

Comparison
----------

A synchronous application processes tasks sequentially for every thread/process it executes, blocking entirely on the result
of the prior call. For Burr, this means that two separate applications have to run in a separate thread/process, and that running
parallel processes have to launch in a multithreaded/multi-processing environment, run, and join the results.

In the case of Burr, this means that you have a 1:1 app -> thread/process mapping (unless you're using :ref:`parallelism <parallelism>` and explicitly multithreading sub-actions).

An asynchronous application can parallelize multiple I/O bound tasks within the confines of a single thread. At the time that
a task blocks on I/O it can give control back to the process, allow it to run other tasks simultaneously.

In the case of Burr, this allows you to run more than one applications,in parallel, on the same thread.
Note, however, that you have to ensure the application is async all the way down -- E.G. that every blocking call
is called using `await` -- if it blocks the event loop through a slow, synchronous call, it will block *all* current
applications.

In general, Burr is equipped to handle both synchronous and asynchronous runs. We usually do that by
providing both methods (see specific references for more detail and reach out if you feel like we
are missing a specific implementation). Furthermore, Burr suports the following APIs for both synchronous/asynchronous interfaces:

- :ref:`hooks <hooksref>`
- :ref:`persisters <persistersref>`

Nuances of Sync + Async together
--------------------------------

We encourage to make a decision to either commit fully to sync or async. That said,
there are cases where a hybrid situation may be desirable or unavoidable (testing, prototyping,
legacy code, ...) and we give some options to handle that. The table bellow shows the
possibilities Burr now supports -- combining the set of synchronous/asynchronous.


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
