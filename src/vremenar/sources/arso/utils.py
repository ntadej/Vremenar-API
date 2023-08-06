"""ARSO weather utils."""
from typing import Any

from vremenar.database.redis import redis
from vremenar.database.stations import get_stations
from vremenar.definitions import CountryID, ObservationType
from vremenar.models.maps import MapType
from vremenar.models.stations import StationBase, StationInfoExtended
from vremenar.models.weather import WeatherCondition
from vremenar.utils import chunker, logger, parse_time, to_timestamp

BASEURL: str = "https://vreme.arso.gov.si"
API_BASEURL: str = "https://vreme.arso.gov.si/api/1.0/"
TIMEOUT: int = 15


async def get_weather_ids_for_timestamp(timestamp: str) -> set[str]:
    """Get ARSO weather IDs for timestamp from redis."""
    ids: set[str] = await redis.smembers(f"arso:weather:{timestamp}")
    return ids


async def get_weather_records(ids: set[str]) -> list[dict[str, Any]]:
    """Get ARSO weather records from redis."""
    result: list[dict[str, Any]] = []

    async with redis.client() as connection:
        for batch in chunker(list(ids), 100):
            async with connection.pipeline(transaction=False) as pipeline:
                for record_id in batch:
                    pipeline.hgetall(record_id)
                response = await pipeline.execute()
            result.extend(response)

    return result


async def get_map_ids_for_type(map_type: MapType) -> list[str]:
    """Get ARSO map IDs for type from redis."""
    ids: list[str] = [
        map_id
        async for map_id in redis.scan_iter(
            match=f"arso:map:{map_type.value}:*",
            count=1000,
        )
    ]
    return ids


async def get_map_data(ids: list[str]) -> list[dict[str, Any]]:
    """Get ARSO map data from redis."""
    result: list[dict[str, Any]] = []

    async with redis.client() as connection:
        async with connection.pipeline(transaction=False) as pipeline:
            for record_id in ids:
                pipeline.hgetall(record_id)
            response = await pipeline.execute()
        result.extend(response)

    return result


async def parse_station(feature: dict[Any, Any]) -> StationInfoExtended | None:
    """Parse ARSO station."""
    stations = await get_stations(CountryID.Slovenia)

    properties = feature["properties"]

    station_id = properties["id"].strip("_")
    return stations.get(station_id, None)


async def parse_record(
    record: dict[str, Any],
    observation: ObservationType,
) -> tuple[StationBase | None, WeatherCondition | None]:
    """Parse ARSO weather record."""
    station_id = record["station_id"]
    stations = await get_stations(CountryID.Slovenia)

    if station_id not in stations:  # pragma: no cover
        return None, None

    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station:  # pragma: no cover
        return None, None

    condition = WeatherCondition(
        observation=observation,
        timestamp=record["timestamp"],
        icon=record["icon"],
        temperature=float(record["temperature"]),
        temperature_low=float(record["temperature_low"])
        if "temperature_low" in record
        else None,
    )

    return station, condition


async def parse_feature(
    feature: dict[Any, Any],
    observation: ObservationType,
) -> tuple[StationInfoExtended | None, WeatherCondition | None]:
    """Parse ARSO feature."""
    stations = await get_stations(CountryID.Slovenia)

    properties = feature["properties"]

    station_id = properties["id"].strip("_")
    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station:  # pragma: no cover
        logger.warning("Unknown ARSO station: %s = %s", station_id, properties["title"])
        return None, None

    timeline = properties["days"][0]["timeline"][0]
    time = parse_time(timeline["valid"])
    icon = timeline["clouds_icon_wwsyn_icon"]

    if "txsyn" in timeline:
        temperature: float = float(timeline["txsyn"])
        temperature_low: float | None = float(timeline["tnsyn"])
    else:
        temperature = float(timeline["t"])
        temperature_low = None

    condition = WeatherCondition(
        observation=observation,
        timestamp=to_timestamp(time),
        icon=icon,
        temperature=temperature,
    )
    if temperature_low:
        condition.temperature_low = temperature_low

    return station, condition
