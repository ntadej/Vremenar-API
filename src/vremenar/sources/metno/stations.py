"""MET.no weather stations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vremenar.exceptions import (
    InvalidSearchQueryException,
    UnknownStationException,
)
from vremenar.models.weather import (
    WeatherInfoExtended,
)

from .utils import (
    encode_station_id,
    get_weather_records,
    parse_record,
    request_weather_record,
)

if TYPE_CHECKING:
    from vremenar.models.stations import (
        StationInfo,
        StationSearchModel,
    )


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate."""
    if query.latitude is None or query.longitude is None:
        err = "Coordinates are required"
        raise InvalidSearchQueryException(err)

    # round to 3 decimals
    query.latitude = round(query.latitude, 3)
    query.longitude = round(query.longitude, 3)

    station_id = encode_station_id(query.latitude, query.longitude)
    try:
        weather_info = await current_station_condition(station_id)
    except UnknownStationException:  # pragma: no cover
        return []

    return [weather_info.station]


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    # try the cache first, if not found, fetch from MET.no API
    records = await get_weather_records({f"met.no:weather:current:{station_id}"})
    if not records:
        records = await request_weather_record(station_id)

    for record in records:
        if not record:  # pragma: no cover
            continue

        station, condition = parse_record(record)
        if not station:  # pragma: no cover
            continue
        if not condition:  # pragma: no cover
            continue

        return WeatherInfoExtended(station=station, condition=condition)

    raise UnknownStationException  # pragma: no cover
