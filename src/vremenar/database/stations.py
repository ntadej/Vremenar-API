"""Stations database helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import asyncstdlib as a

from vremenar.models.common import Coordinate
from vremenar.models.stations import StationInfoExtended

from .redis import redis

if TYPE_CHECKING:
    from vremenar.definitions import CountryID

STATION_BASE_KEYS: set[str] = {
    "id",
    "name",
    "latitude",
    "longitude",
    "altitude",
    "zoom_level",
    "forecast_only",
    "alerts_area",
}


class StationDict(TypedDict, total=False):
    """Station dictionary."""

    id: str
    name: str
    latitude: float
    longitude: float
    altitude: float
    zoom_level: float
    forecast_only: bool
    alerts_area: str


async def load_stations(country: CountryID) -> dict[str, StationDict]:
    """Load stations from redis."""
    stations: dict[str, StationDict] = {}
    async with redis.client() as connection:  # pragma: no branch
        station_ids: set[str] = await redis.smembers(f"station:{country.value}")
        async with connection.pipeline(transaction=False) as pipeline:
            for station_id in station_ids:
                pipeline.hgetall(f"station:{country.value}:{station_id}")
            response = await pipeline.execute()

    for station in response:
        stations[station["id"]] = station

    return stations


@a.lru_cache
async def get_stations(country: CountryID) -> dict[str, StationInfoExtended]:
    """Get a dictionary of supported stations for a country."""
    stations_raw: dict[str, StationDict] = await load_stations(country)
    stations: dict[str, StationInfoExtended] = {}

    for station_id, station in stations_raw.items():
        extra_keys: set[str] = set(station.keys()).difference(STATION_BASE_KEYS)
        metadata = {key: station[key] for key in extra_keys}  # type: ignore

        stations[station_id] = StationInfoExtended(
            id=station_id,
            name=station["name"],
            coordinate=Coordinate(
                latitude=station["latitude"],
                longitude=station["longitude"],
                altitude=station["altitude"],
            ),
            zoom_level=station["zoom_level"],
            forecast_only=station["forecast_only"],
            alerts_area=station.get("alerts_area", None),
            metadata=metadata if metadata else None,
        )
    return dict(sorted(stations.items(), key=lambda item: item[1].name))


async def search_stations(
    country: CountryID,
    latitude: float,
    longitude: float,
) -> list[StationInfoExtended]:
    """Search for stations by coordinate."""
    async with redis.client() as connection:  # pragma: no branch
        station_ids: list[tuple[str, float]] = await redis.geosearch(
            f"location:{country.value}",
            latitude=latitude,
            longitude=longitude,
            radius=50,
            unit="km",
            withdist=True,
            sort="ASC",
        )

        async with connection.pipeline(transaction=False) as pipeline:
            for station_id, _ in station_ids:
                pipeline.hgetall(f"station:{country.value}:{station_id}")
            response = await pipeline.execute()

    stations: list[StationInfoExtended] = []
    for station in response:
        extra_keys: set[str] = set(station.keys()).difference(STATION_BASE_KEYS)
        metadata = {key: station[key] for key in extra_keys}

        stations.append(
            StationInfoExtended(
                id=station["id"],
                name=station["name"],
                coordinate=Coordinate(
                    latitude=station["latitude"],
                    longitude=station["longitude"],
                    altitude=station["altitude"],
                ),
                zoom_level=station["zoom_level"],
                forecast_only=station["forecast_only"],
                alerts_area=station.get("alerts_area", None),
                metadata=metadata if metadata else None,
            ),
        )

    return stations
