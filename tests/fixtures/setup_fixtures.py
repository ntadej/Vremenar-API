"""Setup test database."""
from asyncio import run
from datetime import datetime, timedelta, timezone
from vremenar.database.redis import redis  # type: ignore
from vremenar.definitions import CountryID  # type: ignore
from vremenar.utils import to_timestamp  # type: ignore
from typing import Any


async def store_station(country: CountryID, station: dict[str, Any]) -> None:
    """Store a station to redis."""
    id = station['id']

    async with redis.pipeline() as pipeline:
        pipeline.sadd(f'station:{country.value}', id)
        pipeline.hset(f'station:{country.value}:{id}', mapping=station)
        await pipeline.execute()


async def store_mosmix_record(record: dict[str, Any]) -> None:
    """Store a MOSMIX record to redis."""
    set_key = f"mosmix:{record['timestamp']}"
    key = f"mosmix:{record['timestamp']}:{record['station_id']}"

    async with redis.pipeline() as pipeline:
        pipeline.sadd(set_key, key)
        pipeline.hset(key, mapping=record)
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


async def mosmix_fixtures() -> None:
    """Create and setup MOSMIX fixtures."""
    now = datetime.now(tz=timezone.utc)
    now = now.replace(minute=0, second=0, microsecond=0)
    soon = now + timedelta(hours=1)
    timestamp = to_timestamp(now)
    timestamp_soon = to_timestamp(soon)

    record = {
        'source': 'MOSMIX:2020-12-27T18:00:00.000Z',
        'station_id': '10147',
        'timestamp': timestamp,
        'wind_direction': 148.0,
        'wind_speed': 7.2,
        'wind_gust_speed': 11.83,
        'cloud_cover': 100.0,
        'pressure_msl': 97880.0,
        'precipitation': 0.2,
        'sunshine': 0.0,
        'dew_point': 274.65,
        'temperature': 276.55,
        'visibility': 13900.0,
        'condition': 61.0,
    }

    record_soon = {
        'source': 'MOSMIX:2020-12-27T18:00:00.000Z',
        'station_id': '10147',
        'timestamp': timestamp_soon,
        'wind_direction': 148.0,
        'wind_speed': 7.2,
        'wind_gust_speed': 11.83,
        'cloud_cover': 100.0,
        'pressure_msl': 97880.0,
        'precipitation': 0.2,
        'sunshine': 0.0,
        'dew_point': 274.65,
        'temperature': 276.55,
        'visibility': 13900.0,
        'condition': 61.0,
    }

    await store_mosmix_record(record)
    await store_mosmix_record(record_soon)


async def setup_fixtures() -> None:
    """Create and setup fixtures."""
    await stations_fixtures()
    await mosmix_fixtures()


run(setup_fixtures())
