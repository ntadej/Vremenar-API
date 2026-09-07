"""MET.no weather utils."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any, cast

from httpx2 import AsyncClient, codes

from vremenar import __version__
from vremenar.database.redis import redis
from vremenar.definitions import ObservationType
from vremenar.exceptions import UnknownStationException
from vremenar.models.common import Coordinate
from vremenar.models.stations import StationInfo
from vremenar.models.weather import WeatherCondition
from vremenar.utils import chunker, day_or_night, logger, to_timestamp

if TYPE_CHECKING:
    from collections.abc import Mapping


API_BASEURL = "https://api.met.no/weatherapi/locationforecast/2.0"


def encode_station_id(latitude: float, longitude: float) -> str:
    """Encode station ID for easier usage."""
    return f"MET.no_{latitude}_{longitude}"


def decode_station_id(station_id: str) -> tuple[float, float]:
    """Decode station ID."""
    parts = station_id.split("_")
    if len(parts) != 3 or parts[0] != "MET.no":  # ruff: ignore[magic-value-comparison]
        raise UnknownStationException  # pragma: no cover
    return float(parts[1]), float(parts[2])


def get_icon_base(weather: dict[str, Any]) -> str:
    """Get base icon from weather data."""
    weather_condition = weather.get("symbol_code")
    if weather_condition == "fog":
        return "FG"

    cloud_cover = weather.get("cloud_area_fraction")
    if not cloud_cover:  # pragma: no cover
        cloud_cover = 0

    cloud_cover_fraction = float(cloud_cover) / 100
    if cloud_cover_fraction < 1 / 8:
        return "clear"
    if 1 / 8 <= cloud_cover_fraction < 4 / 8:
        return "partCloudy"
    if 4 / 8 <= cloud_cover_fraction < 7 / 8:
        return "prevCloudy"
    return "overcast"


def get_icon_condition(weather: dict[str, Any]) -> str | None:
    """Get icon condition from weather data."""
    weather_condition = weather.get("symbol_code", "")

    precipitation_intensity = float(weather.get("precipitation_amount", 0.0))
    if precipitation_intensity <= 0:
        return None

    precipitation_heavy_threshold = 10
    precipitation_moderate_threshold = 2.5
    if precipitation_intensity > precipitation_heavy_threshold:
        intensity = "heavy"
    elif precipitation_intensity > precipitation_moderate_threshold:
        intensity = "mod"
    else:
        intensity = "light"

    if "sleet" in weather_condition:
        precipitation_type = "SHGR"
    elif "thunder" in weather_condition:
        precipitation_type = "TSRA"
    elif "snow" in weather_condition:
        precipitation_type = "SN"
    else:
        precipitation_type = "RA"

    return f"{intensity}{precipitation_type}"


def get_icon(weather: dict[str, Any], coordinate: Coordinate, time: datetime) -> str:
    """Get icon from weather data."""
    # SOURCE:
    # conditions: dry, fog, rain, sleet, snow, hail, thunderstorm, null
    #
    # ICONS:
    # time: day/night
    # base: FG, clear, overcast, partCloudy, prevCloudy
    # intensity: light, mod, heavy
    # modifiers: DZ (drizzle), FG (fog), RA (rain), RASN (rain+snow), SN (snow),
    #            SHGR (hail shower), SHRA (rain shower),
    #            SHRASN (rain+snow shower), SHSN (snow shower),
    #            TS (thunderstorm), TSGR(hail thunderstorm), TSRA (rain thunderstorm),
    #            TSRASN(rain+snow thunderstorm), TSSN (snow thunderstorm)
    #
    # CRITERIA:
    # rain:
    #   light - when the precipitation rate is < 2.5 mm per hour
    #   moderate - when the precipitation rate is between 2.5 mm and 10 mm per hour
    #   heavy - when the precipitation rate is > 10 mm per hour
    # sky:
    #   clear - 0 to 1/8
    #   partly cloudy - 1/8 to 4/8
    #   mostly cloudy - 4/8 to 7/8
    #   overcast - 7/8 to 1

    time_of_day = day_or_night(coordinate, time)
    base_icon = get_icon_base(weather)
    condition = get_icon_condition(weather)
    if condition:
        return f"{base_icon}_{condition}_{time_of_day}"
    return f"{base_icon}_{time_of_day}"


async def get_weather_records(ids: set[str]) -> list[dict[str, Any]]:
    """Get MET.no weather records from redis."""
    result: list[dict[str, Any]] = []

    async with redis.client() as connection:
        for batch in chunker(list(ids), 100):
            async with connection.pipeline(transaction=False) as pipeline:
                for record_id in batch:
                    pipeline.hgetall(record_id)
                response = await pipeline.execute()
                # filter out empty records
                response = [record for record in response if record]
            result.extend(response)

    return result


async def write_weather_record(record: dict[str, Any], delta: timedelta) -> None:
    """Write MET.no weather record to redis."""
    record_id = f"met.no:weather:current:{record['station_id']}"
    async with redis.pipeline() as pipeline:
        pipeline.hset(
            record_id,
            mapping=cast("Mapping[bytes | str, bytes | float | int | str]", record),
        )
        pipeline.expire(record_id, time=delta)
        await pipeline.execute()


async def request_weather_record(station_id: str) -> list[dict[str, Any]]:  # ruff: ignore[too-many-locals]
    """Load MET.no weather record from upstream API."""
    latitude, longitude = decode_station_id(station_id)

    api_url = f"{API_BASEURL}/compact?lat={latitude}&lon={longitude}"
    headers = {
        "User-Agent": f"Vremenar-API/{__version__} github.com/ntadej/Vremenar-API",
    }
    logger.debug("MET.no API request: %s", api_url)
    async with AsyncClient() as client:
        response = await client.get(api_url, headers=headers)
        # can be invalid
        if response.status_code != codes.OK:  # pragma: no cover
            raise UnknownStationException  # pragma: no cover
        data: dict[str, Any] = response.json()
        data_headers = response.headers

    now_time = datetime.now(tz=UTC)
    updated_at = data.get("properties", {}).get("meta", {}).get("updated_at", None)
    updated_at_time = datetime.fromisoformat(updated_at) if updated_at else now_time
    expires_at = data_headers.get("expires", None)
    expires_time = parsedate_to_datetime(expires_at) if expires_at else now_time

    series_item = data.get("properties", {}).get("timeseries", [{}])[0]
    series_data = series_item.get("data", {}).get("instant", {}).get("details", {})
    series_summary = series_item.get("data", {}).get("next_1_hours", {})
    series_at = series_item.get("time", None)
    series_time = datetime.fromisoformat(series_at) if series_at else now_time
    station_altitude = data.get("geometry", {}).get("coordinates", [None, None, None])[
        2
    ]

    output: dict[str, Any] = {
        "source": "met.no",
        "station_id": station_id,
        "timestamp": to_timestamp(updated_at_time) if updated_at_time else None,
        "air_pressure_at_sea_level": series_data.get("air_pressure_at_sea_level"),
        "air_temperature": series_data.get("air_temperature"),
        "cloud_area_fraction": series_data.get("cloud_area_fraction"),
        "relative_humidity": series_data.get("relative_humidity"),
        "wind_from_direction": series_data.get("wind_from_direction"),
        "wind_speed": series_data.get("wind_speed"),
        "symbol_code": series_summary.get("summary", {}).get("symbol_code", ""),
        "precipitation_amount": series_summary.get("details", {}).get(
            "precipitation_amount",
            0.0,
        ),
        "station_altitude": station_altitude,
    }
    output["icon"] = get_icon(
        output,
        Coordinate(latitude=latitude, longitude=longitude),
        series_time,
    )

    await write_weather_record(output, expires_time - now_time)

    return [output]


def parse_record(
    record: dict[str, Any],
) -> tuple[StationInfo | None, WeatherCondition | None]:
    """Parse MET.no weather record."""
    station_id = record.get("station_id", "")
    latitude, longitude = decode_station_id(station_id)
    station = StationInfo(
        id=station_id,
        name="",
        coordinate=Coordinate(
            latitude=latitude,
            longitude=longitude,
            altitude=record.get("station_altitude"),
        ),
    )
    condition = WeatherCondition(
        observation=ObservationType.Recent,
        timestamp=record["timestamp"],
        icon=record["icon"],
        temperature=float(record["air_temperature"]),
    )

    return station, condition
