"""Helper utilities."""
from collections.abc import Iterable
from datetime import date, datetime, timezone
from functools import lru_cache
from logging import Logger, getLogger
from typing import Any

from astral import Observer, sun

from .models.common import Coordinate

logger: Logger = getLogger("uvicorn.error")


def chunker(container: list[Any], size: int) -> Iterable[list[Any]]:
    """Loop over a container in chunks."""
    return (container[pos : pos + size] for pos in range(0, len(container), size))


@lru_cache
def sunrise_sunset(
    latitude: float,
    longitude: float,
    date: date,
) -> tuple[datetime, datetime]:
    """Get sunrise and sunset."""
    return sun.daylight(Observer(latitude, longitude), date)


def day_or_night(coordinate: Coordinate, time: datetime) -> str:
    """Get part of day for a specific place."""
    try:
        sunrise, sunset = sunrise_sunset(
            coordinate.latitude,
            coordinate.longitude,
            time.date(),
        )
    except ValueError as e:  # pragma: no cover
        return "day" if "above" in e.args[0] else "night"
    else:
        return "day" if sunrise <= time <= sunset else "night"


def parse_timestamp(timestamp: str) -> datetime:
    """Parse time from timestamp string."""
    return datetime.fromtimestamp(float(timestamp[:-3]), tz=timezone.utc)


def to_timestamp(time: datetime) -> str:
    """Dump timestamp in ms."""
    return f"{int(time.timestamp())}000"
