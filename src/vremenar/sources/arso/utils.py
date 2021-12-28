"""ARSO weather utils."""

from functools import lru_cache
from json import load
from pathlib import Path
from typing import Any, Optional

from ...definitions import ObservationType
from ...models.common import Coordinate
from ...models.stations import StationInfoExtended
from ...models.weather import WeatherCondition
from ...utils import logger, parse_time, to_timestamp

BASEURL: str = 'https://vreme.arso.gov.si'
API_BASEURL: str = 'https://vreme.arso.gov.si/api/1.0/'
TIMEOUT: int = 15


def zoom_level_conversion(zoom_level: Optional[float]) -> Optional[float]:
    """Convert zoom levels from ARSO ones."""
    if zoom_level is not None:
        zoom_level = zoom_level + 1.0 if zoom_level == 5.0 else zoom_level
        zoom_level /= 6
        zoom_epsilon = 0.25
        zoom_level *= 11 - 7.5 - zoom_epsilon
        zoom_level = 11 - zoom_level - zoom_epsilon
        return zoom_level
    return None


def weather_map_url(map_id: str) -> str:
    """Generate forecast map URL."""
    if map_id == 'current':
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json'

    if map_id[0] == 'd':
        return (
            f'{BASEURL}/uploads/probase/www/fproduct/json/sl/forecast_si_{map_id}.json'
        )

    return ''


@lru_cache
def get_stations() -> dict[str, StationInfoExtended]:
    """Get a dictionary of supported ARSO stations."""
    path: Path = Path.cwd() / 'data/stations/ARSO.json'
    stations: dict[str, StationInfoExtended] = {}
    with open(path) as file:
        data = load(file)
        for station in data:
            station_id: str = station['id'].strip('_')
            stations[station_id] = StationInfoExtended(
                id=station_id,
                name=station['title'],
                coordinate=Coordinate(
                    latitude=station['latitude'],
                    longitude=station['longitude'],
                    altitude=station['altitude'],
                ),
                zoom_level=zoom_level_conversion(
                    float(station['zoomLevel']) if 'zoomLevel' in station else None
                ),
            )
    return {k: v for k, v in sorted(stations.items(), key=lambda item: item[1].name)}


def parse_station(feature: dict[Any, Any]) -> Optional[StationInfoExtended]:
    """Parse ARSO station."""
    stations = get_stations()

    properties = feature['properties']

    station_id = properties['id'].strip('_')
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        return None

    return station


def parse_feature(
    feature: dict[Any, Any], observation: ObservationType
) -> tuple[Optional[StationInfoExtended], Optional[WeatherCondition]]:
    """Parse ARSO feature."""
    stations = get_stations()

    properties = feature['properties']

    station_id = properties['id'].strip('_')
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        logger.warning('Unknown ARSO station: %s = %s', station_id, properties['title'])
        return None, None

    timeline = properties['days'][0]['timeline'][0]
    time = parse_time(timeline['valid'])
    icon = timeline['clouds_icon_wwsyn_icon']

    if 'txsyn' in timeline:
        temperature: float = float(timeline['txsyn'])
        temperature_low: Optional[float] = float(timeline['tnsyn'])
    else:
        temperature = float(timeline['t'])
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
