# mypy: disable-error-code="arg-type,import-untyped"
"""Setup test database."""

from __future__ import annotations

from asyncio import run
from datetime import UTC, datetime, timedelta

from vremenar.database.redis import redis
from vremenar.definitions import CountryID, LanguageID
from vremenar.models.maps import MapType
from vremenar.utils import to_timestamp


async def store_station(
    country: CountryID,
    station: dict[str | bytes, str | int | float],
) -> None:
    """Store a station to redis."""
    station_id = station["id"]

    async with redis.pipeline() as pipeline:
        pipeline.sadd(f"station:{country}", station_id)
        pipeline.hset(f"station:{country}:{station_id}", mapping=station)
        pipeline.geoadd(
            f"location:{country}",
            (station["longitude"], station["latitude"], station_id),
        )
        await pipeline.execute()


async def store_arso_weather_record(
    record: dict[str | bytes, str | int | float],
    key_override: str = "",
) -> None:
    """Store an ARSO weather record to redis."""
    if not key_override and isinstance(record["timestamp"], str):
        key_override = record["timestamp"]
    set_key = f"arso:weather:{key_override}"
    key = f"arso:weather:{key_override}:{record['station_id']}"

    async with redis.pipeline() as pipeline:
        pipeline.sadd(set_key, key)
        pipeline.hset(key, mapping=record)
        await pipeline.execute()


async def store_arso_map_record(
    record: dict[str | bytes, str | int | float],
    map_type: str,
    key_override: str = "",
) -> None:
    """Store an ARSO map record to redis."""
    if not key_override and isinstance(record["timestamp"], str):
        key_override = record["timestamp"]
    key = f"arso:map:{map_type}:{key_override}"

    async with redis.pipeline() as pipeline:
        pipeline.hset(key, mapping=record)
        await pipeline.execute()


async def store_mosmix_record(record: dict[str | bytes, str | int | float]) -> None:
    """Store a MOSMIX record to redis."""
    set_key = f"mosmix:{record['timestamp']}"
    key = f"mosmix:{record['timestamp']}:{record['station_id']}"

    async with redis.pipeline() as pipeline:
        pipeline.sadd(set_key, key)
        pipeline.hset(key, mapping=record)
        await pipeline.execute()


async def store_dwd_weather_record(
    record: dict[str | bytes, str | int | float],
) -> None:
    """Store a DWD weather record to redis."""
    key = f"dwd:current:{record['station_id']}"

    async with redis.pipeline() as pipeline:
        pipeline.hset(key, mapping=record)
        await pipeline.execute()


async def store_alerts_areas(
    country: CountryID,
    areas: list[dict[str | bytes, str]],
) -> None:
    """Store alerts areas to redis."""
    async with redis.client() as connection:
        for area in areas:
            async with connection.pipeline() as pipeline:
                pipeline.hset(
                    f"alerts_area:{country}:{area['code']}:info",
                    mapping=area,
                )
                pipeline.sadd(f"alerts_area:{country}", area["code"])
                await pipeline.execute()


async def store_alert_record(
    country: CountryID,
    record: dict[str | bytes, str],
    record_localised: dict[str | bytes, str],
    record_areas: list[str],
) -> None:
    """Store alert record to redis."""
    record_id: str = record["id"]

    async with redis.pipeline() as pipeline:
        pipeline.sadd(f"alert:{country}", record_id)
        pipeline.hset(f"alert:{country}:{record_id}:info", mapping=record)
        if record_areas:
            pipeline.sadd(f"alert:{country}:{record_id}:areas", *record_areas)
        for language in LanguageID:
            pipeline.hset(
                f"alert:{country}:{record_id}:localised_{language}",
                mapping=record_localised,
            )
        for area in record_areas:
            pipeline.sadd(f"alerts_area:{country}:{area}:alerts", record_id)
        await pipeline.execute()


async def stations_fixtures() -> None:
    """Create and setup weather stations fixtures."""
    germany = {
        "id": "10147",
        "name": "Hamburg Fuhlsbüttel",
        "latitude": 53.63,
        "longitude": 10.0,
        "altitude": 16.0,
        "zoom_level": 7.5,
        "forecast_only": 0,
        "alerts_area": "DE413",
        "DWD_ID": "1975",
        "status": "1",
    }
    germany_forecast_only = {
        "id": "P0201",
        "name": "Schenefeld",
        "latitude": 53.6,
        "longitude": 9.82,
        "altitude": 10.0,
        "zoom_level": 8.5,
        "forecast_only": 1,
        "alerts_area": "DE058",
        "status": "1",
    }
    slovenia = {
        "id": "METEO-0038",
        "name": "Bled",
        "latitude": 46.3684,
        "longitude": 14.1101,
        "altitude": 487.0,
        "zoom_level": 10.75,
        "forecast_only": 0,
        "alerts_area": "SI007",
        "region": "SI_GORENJSKA",
        "country": "SI",
    }

    await store_station(CountryID.Germany, germany)
    await store_station(CountryID.Germany, germany_forecast_only)
    await store_station(CountryID.Slovenia, slovenia)


async def arso_fixtures() -> None:
    """Create and setup ARSO fixtures."""
    source = "ARSO:current:00:00.000Z"
    now = datetime.now(tz=UTC)
    now = now.replace(minute=0, second=0, microsecond=0)
    soon = now + timedelta(hours=1)
    timestamp = to_timestamp(now)
    timestamp_soon = to_timestamp(soon)

    record = {
        "source": source,
        "station_id": "METEO-0038",
        "timestamp": timestamp,
        "icon": "prevCloudy_day",
        "temperature": 12,
    }

    record_soon = {
        "source": source,
        "station_id": "METEO-0038",
        "timestamp": timestamp_soon,
        "icon": "overcast_lightRA_day",
        "temperature": 32,
        "temperature_low": 13,
    }

    record_unknown = {
        "source": source,
        "station_id": "NULL",
        "timestamp": timestamp,
        "icon": "prevCloudy_day",
        "temperature": 12,
    }

    await store_arso_weather_record(record, "current")
    await store_arso_weather_record(record_soon)
    await store_arso_weather_record(record_unknown)

    map_record = {
        "timestamp": timestamp,
        "url": "foo",
        "observation": "recent",
    }
    await store_arso_map_record(map_record, MapType.WeatherCondition, "current")

    for map_type in [
        MapType.Precipitation,
        MapType.CloudCoverage,
        MapType.WindSpeed,
        MapType.Temperature,
        MapType.HailProbability,
    ]:
        await store_arso_map_record(map_record, map_type)


async def dwd_fixtures() -> None:
    """Create and setup DWD fixtures."""
    now = datetime.now(tz=UTC)
    now = now.replace(minute=0, second=0, microsecond=0)
    timestamp = to_timestamp(now)

    record = {
        "station_id": "10147",
        "timestamp": timestamp,
        "wind_direction": 148.0,
        "wind_speed": 7.2,
        "wind_gust_speed": 11.83,
        "cloud_cover": 100.0,
        "pressure_msl": 97880.0,
        "precipitation": 50.0,
        "sunshine": 0.0,
        "dew_point": 274.65,
        "temperature": 276.55,
        "visibility": 13900.0,
        "condition": "rain",
    }

    await store_dwd_weather_record(record)


async def mosmix_fixtures() -> None:
    """Create and setup MOSMIX fixtures."""
    source = "MOSMIX:2020-12-27T18:00:00.000Z"
    now = datetime.now(tz=UTC)
    now = now.replace(minute=0, second=0, microsecond=0)
    soon = now + timedelta(hours=1)
    timestamp = to_timestamp(now)
    timestamp_soon = to_timestamp(soon)

    record = {
        "source": source,
        "station_id": "10147",
        "timestamp": timestamp,
        "wind_direction": 148.0,
        "wind_speed": 7.2,
        "wind_gust_speed": 11.83,
        "cloud_cover": 100.0,
        "pressure_msl": 97880.0,
        "precipitation": 50.0,
        "sunshine": 0.0,
        "dew_point": 274.65,
        "temperature": 276.55,
        "visibility": 13900.0,
        "condition": "rain",
    }

    record_soon = {
        "source": source,
        "station_id": "10147",
        "timestamp": timestamp_soon,
        "wind_direction": 148.0,
        "wind_speed": 7.2,
        "wind_gust_speed": 11.83,
        "cloud_cover": 100.0,
        "pressure_msl": 97880.0,
        "precipitation": 0.2,
        "sunshine": 0.0,
        "dew_point": 274.65,
        "temperature": 276.55,
        "visibility": 13900.0,
        "condition": "dry",
    }

    record_unknown = {
        "source": source,
        "station_id": "NULL",
        "timestamp": timestamp,
        "wind_direction": 148.0,
        "wind_speed": 7.2,
        "wind_gust_speed": 11.83,
        "cloud_cover": 100.0,
        "pressure_msl": 97880.0,
        "precipitation": 0.2,
        "sunshine": 0.0,
        "dew_point": 274.65,
        "temperature": 276.55,
        "visibility": 13900.0,
        "condition": "dry",
    }

    await store_mosmix_record(record)
    await store_mosmix_record(record_soon)
    await store_mosmix_record(record_unknown)


async def alerts_fixtures() -> None:
    """Create and setup weather alerts fixtures."""
    area_germany_1: dict[str | bytes, str] = {
        "code": "DE048",
        "name": "Kreis Pinneberg",
        "polygons": "[]",
    }

    area_germany_2: dict[str | bytes, str] = {
        "code": "DE413",
        "name": "Hansestadt Hamburg",
        "polygons": "[]",
    }

    alert_germany_1: dict[str | bytes, str] = {
        "id": "2.49.0.0.276.0.DWD.PVW.TEST",
        "response_type": "prepare",
        "urgency": "immediate",
        "type": "wind",
        "expires": "1762253200000",  # make expiry date far in the future
        "certainty": "likely",
        "severity": "minor",
        "onset": "1662220920000",
    }
    alert_germany_1_areas = ["DE048"]
    alert_germany_1_localised: dict[str | bytes, str] = {
        "event": "wind gusts",
        "sender_name": "Deutscher Wetterdienst",
        "description": (
            "There is a risk of wind gusts (level 1 of 4).\n"
            "Max. gusts: ~ 55 km/h; Wind direction: east"
        ),
        "instructions": "",
        "headline": "Official WARNING of WIND GUSTS",
        "web": "https://www.wettergefahren.de",
    }

    alert_germany_2: dict[str | bytes, str] = {
        "id": "2.49.0.0.277.0.DWD.PVW.TEST",
        "response_type": "prepare",
        "urgency": "immediate",
        "type": "wind",
        "expires": "1762253200000",  # make expiry date far in the future
        "certainty": "likely",
        "severity": "minor",
        "onset": "1662220920000",
    }
    alert_germany_2_localised: dict[str | bytes, str] = {
        "event": "wind gusts",
        "instructions": "RUN!",
        "headline": "Official WARNING of WIND GUSTS",
    }

    alert_slovenia_1: dict[str | bytes, str] = {
        "id": "ARSO.TEST",
        "response_type": "prepare",
        "urgency": "immediate",
        "type": "wind",
        "expires": "1652220920000",  # make expiry date in the past
        "certainty": "likely",
        "severity": "minor",
        "onset": "1652220920000",
    }
    alert_slovenia_1_localised: dict[str | bytes, str] = {
        "event": "wind gusts",
        "headline": "Official WARNING of WIND GUSTS",
    }

    await store_alerts_areas(CountryID.Germany, [area_germany_1, area_germany_2])
    await store_alert_record(
        CountryID.Germany,
        alert_germany_1,
        alert_germany_1_localised,
        alert_germany_1_areas,
    )
    await store_alert_record(
        CountryID.Germany,
        alert_germany_2,
        alert_germany_2_localised,
        [],
    )
    await store_alert_record(
        CountryID.Slovenia,
        alert_slovenia_1,
        alert_slovenia_1_localised,
        [],
    )


async def setup_fixtures() -> None:
    """Create and setup fixtures."""
    await stations_fixtures()
    await arso_fixtures()
    await dwd_fixtures()
    await mosmix_fixtures()
    await alerts_fixtures()


run(setup_fixtures())
