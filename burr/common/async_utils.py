import inspect
from typing import AsyncGenerator, AsyncIterable, Generator, List, TypeVar, Union

T = TypeVar("T")

GenType = TypeVar("GenType")
ReturnType = TypeVar("ReturnType")

SyncOrAsyncIterable = Union[AsyncIterable[T], List[T]]
SyncOrAsyncGenerator = Union[Generator[GenType, None, None], AsyncGenerator[GenType, None]]
SyncOrAsyncGeneratorOrItemOrList = Union[SyncOrAsyncGenerator[GenType], List[GenType], GenType]


async def asyncify_generator(
    generator: SyncOrAsyncGenerator[GenType],
) -> AsyncGenerator[GenType, None]:
    """Convert a sync generator to an async generator.

    :param generator: sync generator
    :return: async generator
    """
    if inspect.isasyncgen(generator):
        async for item in generator:
            yield item
    else:
        for item in generator:
            yield item


async def arealize(maybe_async_generator: SyncOrAsyncGenerator[GenType]) -> List[GenType]:
    """Realize an async generator or async iterable to a list.

    :param maybe_async_generator: async generator or async iterable
    :return: list
    """
    if inspect.isasyncgen(maybe_async_generator):
        out = [item async for item in maybe_async_generator]
    else:
        out = [item for item in maybe_async_generator]
    return out
