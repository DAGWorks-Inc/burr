import concurrent.futures

import ray


class RayExecutor(concurrent.futures.Executor):
    def __init__(self):
        # if not ray.is_initialized(**ray_init_kwargs):
        #     ray.init()
        pass

    def submit(self, fn, *args, **kwargs):
        if not ray.is_initialized():
            raise RuntimeError("Ray is not initialized")

        ray_fn = ray.remote(fn)
        object_ref = ray_fn.remote(*args, **kwargs)
        future = object_ref.future()

        return future

    def shutdown(self, wait=True, **kwargs):
        if ray.is_initialized():
            ray.shutdown()
