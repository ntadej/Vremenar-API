"""Tests configuration."""
import asyncio
import pytest

from httpx import AsyncClient
from typing import Any, AsyncGenerator, Generator


@pytest.fixture(scope='session')
def event_loop(request: Any) -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
# @pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async testing client for unit tests."""
    from vremenar.main import app

    async with AsyncClient(app=app, base_url='http://testserver') as client:
        yield client
