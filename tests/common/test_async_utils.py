from typing import AsyncGenerator, Generator

from burr.common.async_utils import arealize, asyncify_generator


async def test_asyncify_generator_with_sync_generator():
    def sync_gen() -> Generator[int, None, None]:
        for i in range(5):
            yield i

    generator = sync_gen()
    async_generator = asyncify_generator(generator)

    result = [item async for item in async_generator]
    assert result == [0, 1, 2, 3, 4], "Should convert sync generator to async generator"


async def test_asyncify_generator_with_async_generator():
    async def async_gen() -> AsyncGenerator[int, None]:
        for i in range(5):
            yield i

    generator = async_gen()
    async_generator = asyncify_generator(generator)

    result = [item async for item in async_generator]
    assert result == [0, 1, 2, 3, 4], "Should pass through async generator unchanged"


# Test cases for arealize
async def test_arealize_with_sync_generator():
    def sync_gen() -> Generator[int, None, None]:
        for i in range(5):
            yield i

    generator = sync_gen()
    result = await arealize(generator)
    assert result == [0, 1, 2, 3, 4], "Should convert sync generator to list"


async def test_arealize_with_async_generator():
    async def async_gen() -> AsyncGenerator[int, None]:
        for i in range(5):
            yield i

    generator = async_gen()
    result = await arealize(generator)
    assert result == [0, 1, 2, 3, 4], "Should realize async generator to list"


# Edge cases
async def test_asyncify_generator_empty_sync_generator():
    def sync_gen() -> Generator[int, None, None]:
        if False:  # No items to yield
            yield

    generator = sync_gen()
    async_generator = asyncify_generator(generator)

    result = [item async for item in async_generator]
    assert result == [], "Should handle empty sync generator"


async def test_arealize_empty_sync_generator():
    def sync_gen() -> Generator[int, None, None]:
        if False:  # No items to yield
            yield

    generator = sync_gen()
    result = await arealize(generator)
    assert result == [], "Should handle empty sync generator to list"


async def test_asyncify_generator_empty_async_generator():
    async def async_gen() -> AsyncGenerator[int, None]:
        if False:  # No items to yield
            yield

    generator = async_gen()
    async_generator = asyncify_generator(generator)

    result = [item async for item in async_generator]
    assert result == [], "Should handle empty async generator"


async def test_arealize_empty_async_generator():
    async def async_gen() -> AsyncGenerator[int, None]:
        if False:  # No items to yield
            yield

    generator = async_gen()
    result = await arealize(generator)
    assert result == [], "Should handle empty async generator to list"
