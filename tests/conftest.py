"""Tests configuration."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_asyncio import is_async_test


def pytest_collection_modifyitems(items: list[Any]) -> None:
    """Add session scope to async tests."""
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(loop_scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async testing client for unit tests."""
    from vremenar.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
