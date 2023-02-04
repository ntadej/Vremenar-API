"""ARSO weather utils."""
from typing import Any

from ...definitions import CountryID, ObservationType
from ...database.stations import get_stations
from ...models.maps import MapType
from ...models.stations import StationInfoExtended
from ...models.weather import WeatherCondition
from ...utils import join_url, logger, parse_time, to_timestamp

BASEURL: str = "https://vreme.arso.gov.si"
API_BASEURL: str = "https://vreme.arso.gov.si/api/1.0/"
TIMEOUT: int = 15


def weather_map_url(map_id: str) -> str:
    """Generate forecast map URL."""
    if map_id == "current":
        return f"{BASEURL}/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json"

    if map_id[0] == "d":
        return (
            f"{BASEURL}/uploads/probase/www/fproduct/json/sl/forecast_si_{map_id}.json"
        )

    return ""


def weather_map_response_url(map_type: MapType, path: str) -> str:
    """Generate forecast map response URL."""
    if map_type == MapType.WeatherCondition:
        if "nowcast" in path:
            url = path.replace(
                "/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json",
                "/stations/map/current",
            )
        else:
            url = path.replace(
                "/uploads/probase/www/fproduct/json/sl/forecast_si_",
                "/stations/map/",
            )
            url = url.replace(".json", "")
        url += f"?country={CountryID.Slovenia.value}"
        return url

    return join_url(BASEURL, path)


async def parse_station(feature: dict[Any, Any]) -> StationInfoExtended | None:
    """Parse ARSO station."""
    stations = await get_stations(CountryID.Slovenia)

    properties = feature["properties"]

    station_id = properties["id"].strip("_")
    return stations.get(station_id, None)


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
