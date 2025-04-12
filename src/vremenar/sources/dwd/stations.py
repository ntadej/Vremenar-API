"""DWD weather stations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vremenar.database.stations import get_stations, search_stations
from vremenar.definitions import CountryID, ObservationType
from vremenar.exceptions import InvalidSearchQueryException, UnknownStationException
from vremenar.models.weather import WeatherInfoExtended

from .utils import get_weather_records, parse_record

if TYPE_CHECKING:
    from vremenar.models.stations import (
        StationInfo,
        StationInfoExtended,
        StationSearchModel,
    )


async def list_stations() -> list[StationInfoExtended]:
    """List DWD weather stations."""
    stations = await get_stations(CountryID.Germany)
    return list(stations.values())


async def find_station(
    query: StationSearchModel,
    include_forecast_only: bool,
) -> list[StationInfo]:
    """Find station by coordinate."""
    if query.latitude is None or query.longitude is None:
        err = "Coordinates are required"
        raise InvalidSearchQueryException(err)

    stations = await search_stations(
        CountryID.Germany,
        query.latitude,
        query.longitude,
    )

    stations_filtered = [
        station.info()
        for station in stations
        if (include_forecast_only or not station.forecast_only)
        and not (station.metadata and station.metadata["status"] != "1")
    ]

    has_current = any(not station.forecast_only for station in stations)
    if include_forecast_only and not has_current:  # pragma: no cover
        return (
            stations_filtered[:5]
            + [
                station.info()
                for station in stations
                if not station.forecast_only
                and not (station.metadata and station.metadata["status"] != "1")
            ][:1]
        )

    return stations_filtered[:5]


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = await get_stations(CountryID.Germany)
    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station or station.forecast_only:
        raise UnknownStationException

    records = await get_weather_records({f"dwd:current:{station_id}"})

    for record in records:
        if not record:  # pragma: no cover
            continue

        _, condition = await parse_record(record, ObservationType.Recent)
        if not condition:  # pragma: no cover
            continue

        return WeatherInfoExtended(station=station, condition=condition)

    raise UnknownStationException  # pragma: no cover
