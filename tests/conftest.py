"""Tests configuration."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# def pytest_collection_modifyitems(items: list[Any]) -> None:
#     """Add session scope to async tests."""
#     pytest_asyncio_tests = (item for item in items if is_async_test(item))
#     session_scope_marker = pytest.mark.asyncio(scope="session")
#     for async_test in pytest_asyncio_tests:
#         async_test.add_marker(session_scope_marker)


@pytest.fixture(scope="session")
def event_loop(
    request: Any,  # noqa: ANN401, ARG001
) -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async testing client for unit tests."""
    from vremenar.main import app

    transport = ASGITransport(app=app)  # type: ignore
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
