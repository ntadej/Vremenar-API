"""Helper utilities."""

from astral import Observer, sun  # type: ignore
from datetime import date, datetime
from functools import lru_cache
from logging import Logger, getLogger
from typing import Tuple, cast

from .models.common import Coordinate


logger: Logger = getLogger('uvicorn.error')


def join_url(*args: str, trailing_slash: bool = False) -> str:
    """Join url."""
    url = '/'.join(arg.strip('/') for arg in args)
    if trailing_slash:
        return f'{url}/'
    return url


@lru_cache
def sunrise_sunset(
    latitude: float, longitude: float, date: date
) -> Tuple[datetime, datetime]:
    """Get sunrise and sunset."""
    return cast(
        Tuple[datetime, datetime],
        sun.daylight(Observer(latitude, longitude), date),
    )


def day_or_night(coordinate: Coordinate, time: datetime) -> str:
    """Get part of day for a specific place."""
    try:
        sunrise, sunset = sunrise_sunset(
            coordinate.latitude, coordinate.longitude, time.date()
        )
    except ValueError as e:
        return 'day' if 'above' in e.args[0] else 'night'
    else:
        return 'day' if sunrise <= time <= sunset else 'night'


def parse_time(time: str) -> datetime:
    """Parse time from standard string."""
    return datetime.strptime(time, '%Y-%m-%dT%H:%M:%S%z')


def to_timestamp(time: datetime) -> str:
    """Dump timestamp in ms."""
    return f'{str(int(time.timestamp()))}000'
