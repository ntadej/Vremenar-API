"""Setup test database."""
from asyncio import run
from vremenar.database.redis import redis  # type: ignore
from vremenar.definitions import CountryID  # type: ignore
from typing import Any


async def store_station(country: CountryID, station: dict[str, Any]) -> None:
    """Store a station to redis."""
    id = station['id']

    async with redis.pipeline() as pipeline:
        pipeline.sadd(f'station:{country.value}', id)
        pipeline.hset(f'station:{country.value}:{id}', mapping=station)
        await pipeline.execute()


async def stations_fixtures() -> None:
    """Create and setup weather stations fixtures."""
    germany = {
        'id': '10147',
        'name': 'Hamburg Fuhlsbüttel',
        'latitude': 53.63,
        'longitude': 10.0,
        'altitude': 16.0,
        'zoom_level': 7.5,
        'forecast_only': 0,
        'alerts_area': 'DE413',
        'DWD_ID': '1975',
        'status': '1',
    }
    slovenia = {
        'id': 'METEO-0038',
        'name': 'Bled',
        'latitude': 46.3684,
        'longitude': 14.1101,
        'altitude': 487.0,
        'zoom_level': 10.75,
        'forecast_only': 0,
        'alerts_area': 'SI007',
        'region': 'SI_GORENJSKA',
        'country': 'SI',
    }

    await store_station(CountryID.Germany, germany)
    await store_station(CountryID.Slovenia, slovenia)


run(stations_fixtures())
