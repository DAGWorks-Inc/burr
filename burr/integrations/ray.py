import concurrent.futures

import ray


class RayExecutor(concurrent.futures.Executor):
    """Ray parallel executor -- implementation of concurrent.futures.Executor.
    Currently experimental"""

    def __init__(self, shutdown_on_end: bool = False):
        """Creates a Ray executor -- remember to call ray.init() before running anything!"""
        self.shutdown_on_end = shutdown_on_end

    def submit(self, fn, *args, **kwargs):
        """Submits to ray -- creates a python future by calling ray.remote

        :param fn: Function to submit
        :param args: Args for the fn
        :param kwargs: Kwargs for the fn
        :return: The future for the fn
        """
        if not ray.is_initialized():
            raise RuntimeError("Ray is not initialized. Call ray.init() before running anything!")
        ray_fn = ray.remote(fn)
        object_ref = ray_fn.remote(*args, **kwargs)
        future = object_ref.future()

        return future

    def shutdown(self, wait=True, **kwargs):
        """Shuts down the executor by shutting down ray

        :param wait: Whether to wait -- required for hte API but not respected (yet)
        :param kwargs: Keyword arguments -- not used yet
        """
        if self.shutdown_on_end:
            if ray.is_initialized():
                ray.shutdown()
