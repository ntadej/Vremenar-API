"""ARSO weather utils."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import TYPE_CHECKING, Any

from vremenar.database.redis import redis
from vremenar.database.stations import get_stations
from vremenar.definitions import CountryID, ObservationType
from vremenar.models.weather import WeatherCondition, WeatherStatistics
from vremenar.utils import chunker

if TYPE_CHECKING:
    from vremenar.models.maps import MapType
    from vremenar.models.stations import StationBase, StationInfoExtended


async def get_weather_ids_for_timestamp(timestamp: str) -> set[str]:
    """Get ARSO weather IDs for timestamp from redis."""
    ids: set[str] = await redis.smembers(f"arso:weather:{timestamp}")
    return ids


async def get_weather_ids_for_station(station_id: str) -> set[str]:
    """Get ARSO weather IDs for station from redis."""
    ids: set[str] = {
        weather_id
        async for weather_id in redis.scan_iter(
            match=f"arso:weather_48h:*:{station_id}",
            count=1000,
        )
    }
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

    async with (
        redis.client() as connection,
        connection.pipeline(transaction=False) as pipeline,
    ):
        for record_id in ids:
            pipeline.hgetall(record_id)
        response = await pipeline.execute()
    result.extend(response)

    return result


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


def generate_statistics(records: list[dict[str, Any]]) -> WeatherStatistics:
    """Generate weather statistics."""
    records_sorted = sorted(
        records,
        key=lambda x: int(x["timestamp"][:-3]),
        reverse=True,
    )
    for record in records_sorted:
        record["date"] = datetime.fromtimestamp(int(record["timestamp"][:-3]), tz=UTC)
    latest = records_sorted[0]["date"]
    reference_24 = latest + timedelta(hours=-24)
    reference_48 = latest + timedelta(hours=-48)

    records_24h = [
        record for record in records_sorted if record["date"] >= reference_24
    ]
    records_48h = [
        record for record in records_sorted if record["date"] >= reference_48
    ]
    temperatures_24h = [float(r["temperature"]) for r in records_24h]
    temperatures_48h = [float(r["temperature"]) for r in records_48h]

    temperature_min_24h = min(temperatures_24h)
    timestamp_temperature_min_24h = records_24h[
        temperatures_24h.index(temperature_min_24h)
    ]["timestamp"]
    temperature_max_24h = max(temperatures_24h)
    timestamp_temperature_max_24h = records_24h[
        temperatures_24h.index(temperature_max_24h)
    ]["timestamp"]

    return WeatherStatistics(
        timestamp=records_sorted[0]["timestamp"],
        temperature_average_24h=round(mean(temperatures_24h), 1),
        temperature_average_48h=round(mean(temperatures_48h), 1),
        temperature_min_24h=temperature_min_24h,
        temperature_max_24h=temperature_max_24h,
        timestamp_temperature_min_24h=timestamp_temperature_min_24h,
        timestamp_temperature_max_24h=timestamp_temperature_max_24h,
    )
