"""Redis utilities."""

from __future__ import annotations

from os import getenv

from redis.asyncio import Redis, from_url

from vremenar.utils import logger

db_env: str = getenv("VREMENAR_DATABASE", "staging")
database: int = {
    "staging": 0,
    "production": 1,
    "test": 2,
}.get(db_env, 0)
database_host: str = getenv("VREMENAR_DATABASE_HOST", "localhost")

redis: Redis[str] = from_url(
    f"redis://{database_host}/{database}",
    decode_responses=True,
)


def database_info() -> None:
    """Log the database info."""
    logger.debug("Using %s database with ID %d", db_env, database)


__all__ = ["Redis", "redis"]
