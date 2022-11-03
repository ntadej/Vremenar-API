"""Redis utilities."""
from redis.asyncio import Redis, from_url
from os import getenv
from typing import Any

from ..utils import logger

db_env: str = getenv('VREMENAR_DATABASE', 'staging')
database: int = {
    'staging': 0,
    'production': 1,
    'test': 2,
}.get(db_env, 0)

redis: Redis = from_url(  # type: ignore
    f'redis://localhost/{database}', decode_responses=True
)


def database_info() -> None:
    """Log the database info."""
    logger.debug('Using %s database with ID %d', db_env, database)


class BatchedRedis:
    """Put items to redis in batches."""

    def __init__(self, connection: 'Redis[Any]', limit: int | None = 1000) -> None:
        """Initialise with DB."""
        self.connection = connection
        self.queue: list[Any] = []
        self.limit = limit

    async def __aenter__(self) -> 'BatchedRedis':
        """Context manager init."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self._drain()

    async def add(self, item: Any) -> None:
        """Put item to the DB (add it in the queue)."""
        if len(self.queue) == self.limit:
            await self._drain()

        self.queue.append(item)

    def process(self, pipeline: 'Redis[Any]', item: Any) -> None:
        """Process items in queue."""
        raise NotImplementedError(
            'BatchedRedis needs to be subclassed and process implemented'
        )

    async def _drain(self) -> None:
        """Drain the queue."""
        if self.connection and self.queue:
            async with self.connection.pipeline() as pipeline:
                for item in self.queue:
                    self.process(pipeline, item)
                await pipeline.execute()
        self.queue.clear()


__all__ = ['redis', 'Redis', 'BatchedRedis']
