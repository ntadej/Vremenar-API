"""Stations database helpers."""
import asyncstdlib as a
from typing_extensions import TypedDict

from vremenar.definitions import CountryID
from vremenar.models.common import Coordinate
from vremenar.models.stations import StationInfoExtended

from .redis import redis


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
    async with redis.client() as connection:
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
    base_keys: set[str] = {
        "id",
        "name",
        "latitude",
        "longitude",
        "altitude",
        "zoom_level",
        "forecast_only",
        "alerts_area",
    }

    for station_id, station in stations_raw.items():
        extra_keys: set[str] = set(station.keys()).difference(base_keys)
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
            alerts_area=station["alerts_area"] if "alerts_area" in station else None,
            metadata=metadata if metadata else None,
        )
    return dict(sorted(stations.items(), key=lambda item: item[1].name))
