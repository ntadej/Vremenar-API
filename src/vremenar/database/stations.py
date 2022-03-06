"""Stations database helpers."""
import asyncstdlib as a
from typing import Union

from ..definitions import CountryID
from ..models.common import Coordinate
from ..models.stations import StationInfoExtended

from .redis import redis


async def load_stations(
    country: CountryID,
) -> dict[str, dict[str, Union[str, int, float]]]:
    """Load stations from redis."""
    stations: dict[str, dict[str, Union[str, int, float]]] = {}
    async with redis.client() as connection:
        ids: set[str] = await redis.smembers(f'station:{country.value}')
        async with connection.pipeline(transaction=False) as pipeline:
            for id in ids:
                pipeline.hgetall(f'station:{country.value}:{id}')
            response = await pipeline.execute()

    for station in response:
        stations[station['id']] = station

    return stations


@a.lru_cache
async def get_stations(country: CountryID) -> dict[str, StationInfoExtended]:
    """Get a dictionary of supported stations for a country."""
    stations_raw: dict[str, dict[str, Union[str, int, float]]] = await load_stations(
        country
    )
    stations: dict[str, StationInfoExtended] = {}
    base_keys: set[str] = {
        'id',
        'name',
        'latitude',
        'longitude',
        'altitude',
        'zoom_level',
        'forecast_only',
        'alerts_area',
    }

    for id, station in stations_raw.items():
        extra_keys = set(station.keys()).difference(base_keys)
        metadata = None
        if extra_keys:
            metadata = {key: station[key] for key in extra_keys}

        stations[id] = StationInfoExtended(
            id=id,
            name=station['name'],
            coordinate=Coordinate(
                latitude=station['latitude'],
                longitude=station['longitude'],
                altitude=station['altitude'],
            ),
            zoom_level=station['zoom_level'],
            forecast_only=station['forecast_only'],
            alerts_area=station['alerts_area'] if 'alerts_area' in station else None,
            metadata=metadata,
        )
    return {k: v for k, v in sorted(stations.items(), key=lambda item: item[1].name)}
