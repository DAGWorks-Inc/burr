import asyncio
from typing import Awaitable, TypeVar

AwaitableType = TypeVar("AwaitableType")


async def gather_with_concurrency(n, *coros: Awaitable[AwaitableType]) -> tuple[AwaitableType, ...]:
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro: Awaitable[AwaitableType]) -> AwaitableType:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))
