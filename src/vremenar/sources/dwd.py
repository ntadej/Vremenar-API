"""DWD weather source."""

from csv import reader
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from json import load
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import MapLayer, MapType
from ..models.stations import StationInfo
from ..models.weather import WeatherCondition, WeatherInfo
from ..units import kelvin_to_celsius

CACHE_PATH: Path = Path.cwd() / '.cache/dwd'
MAPS_BASEURL = 'https://maps.dwd.de/geoserver/dwd/ows?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true'  # noqa E501


@lru_cache
def get_dwd_stations() -> Dict[str, StationInfo]:
    """Get a dictionary of supported DWD stations."""
    path: Path = Path.cwd() / 'data/stations/DWD.csv'
    stations: Dict[str, StationInfo] = {}
    with open(path, newline='') as csvfile:
        csv = reader(csvfile, dialect='excel')
        next(csv)  # Skip header row.
        for row in csv:
            station_id: str = row[0]
            stations[station_id] = StationInfo(
                id=station_id,
                name=row[3],
                coordinate=Coordinate(latitude=row[4], longitude=row[5]),
                zoom_level=None,  # TODO: zoom level (6, 7)
                metadata={'DWD_ID': row[1]},
            )
    return stations


def list_stations() -> List[StationInfo]:
    """List DWD weather stations."""
    return list(get_dwd_stations().values())


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get DWD map layers."""
    layers: List[MapLayer] = []

    if map_type == MapType.WeatherCondition:
        country_suffix = f'?country={CountryID.Germany}'

        url = '/stations/map/current'
        url += country_suffix
        layers.append(
            MapLayer(
                url=url,
                timestamp=str(int(datetime.now().timestamp())) + '000',
                observation=ObservationType.Recent,
            )
        )
        return layers, []

    if map_type != MapType.Precipitation:
        return [], []

    current_time = datetime.utcnow()
    current_now = datetime.now()
    utc_delta = (current_now - current_time).seconds
    time_delta = timedelta(
        minutes=current_time.minute % 5,
        seconds=current_time.second,
        microseconds=current_time.microsecond,
    )
    current_time -= time_delta
    if time_delta.seconds < 100:  # buffer for recent image
        current_time -= timedelta(minutes=5)
    test_time = current_time.isoformat()
    test_url = f'{MAPS_BASEURL}&layers=dwd:RX-Produkt&bbox=5,50,6,51&width=100&height=100&time={test_time}.000Z'  # noqa E501

    print(test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url)

    if 'InvalidDimensionValue' in response.text:
        print('Current map not available yet')
        current_time -= timedelta(minutes=5)

    # historical data + recent
    for i in range(18, -1, -1):
        time = current_time - timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:RX-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(
                url=url,
                timestamp=str(int(time.timestamp())) + '000',
                observation=ObservationType.Historical
                if i != 0
                else ObservationType.Recent,
            )
        )
    # forecast
    for i in range(1, 19, 1):
        time = current_time + timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:WN-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(
                url=url,
                timestamp=str(int(time.timestamp())) + '000',
                observation=ObservationType.Forecast,
            )
        )

    return layers, []


def _weather_map_url(id: str) -> Path:
    paths = sorted(list(CACHE_PATH.glob('MOSMIX*.json')))
    now = datetime.utcnow()
    for path in paths:
        date = datetime.strptime(path.name, 'MOSMIX:%Y-%m-%dT%H:%M:%S.json')
        delta = (date - now).total_seconds()

        if delta < 0:
            continue

        return path
    return paths[0]


def _parse_record(
    record: Dict[str, Any], observation: ObservationType
) -> Tuple[Optional[StationInfo], Optional[WeatherCondition]]:
    station_id = record['wmo_station_id']
    stations = get_dwd_stations()

    if station_id not in stations:
        return (None, None)

    station = stations[station_id]

    condition = WeatherCondition(
        observation=observation,
        timestamp=record['timestamp'],
        icon='clear',  # TODO: icon
        temperature=kelvin_to_celsius(record['temperature']),
    )

    return (station, condition)


async def get_weather_map(id: str) -> List[WeatherInfo]:
    """Get weather map from ID."""
    path: Path = _weather_map_url(id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    print(path)

    with open(path, 'r') as file:
        records = load(file)

    conditions_list = []
    for record in records:
        station, condition = _parse_record(
            record,
            ObservationType.Recent if id == 'current' else ObservationType.Forecast,
        )
        if not station:
            continue
        conditions_list.append(WeatherInfo(station=station, condition=condition))

    return conditions_list


__all__ = ['get_map_layers', 'get_weather_map']
