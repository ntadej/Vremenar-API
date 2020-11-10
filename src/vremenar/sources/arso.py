"""ARSO weather source."""

from datetime import datetime
from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from json import load
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import MapLayer, MapType, WeatherInfo
from ..models.stations import ExtendedStationInfo, StationInfo, StationSearchModel
from ..models.weather import WeatherCondition
from ..utils import join_url

BASEURL: str = 'https://vreme.arso.gov.si'
API_BASEURL: str = 'https://vreme.arso.gov.si/api/1.0/'

MAP_URL = {
    MapType.WeatherCondition: '/forecast_si_data/',
    MapType.Precipitation: '/inca_precip_data/',
    MapType.CloudCoverage: '/inca_cloud_data/',
    MapType.WindSpeed: '/inca_wind_data/',
    MapType.Temperature: '/inca_t2m_data/',
    MapType.HailProbability: '/inca_hail_data/',
}


def _zoom_level_conversion(zoom_level: Optional[float]) -> Optional[float]:
    if zoom_level is not None:
        zoom_level = zoom_level + 1.0 if zoom_level == 5.0 else zoom_level
        zoom_level /= 6
        zoom_epsilon = 0.25
        zoom_level *= 11 - 7.5 - zoom_epsilon
        zoom_level = 11 - zoom_level - zoom_epsilon
        return zoom_level
    return None


def _weather_map_url(id: str) -> str:
    if id == 'current':
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json'
    else:
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/forecast_si_{id}.json'


@lru_cache
def get_arso_stations() -> Dict[str, StationInfo]:
    """Get a dictionary of supported ARSO stations."""
    path: Path = Path.cwd() / 'data/stations/ARSO.json'
    stations: Dict[str, StationInfo] = {}
    with open(path, 'r') as file:
        data = load(file)
        for station in data:
            station_id: str = station['id'].strip('_')
            stations[station_id] = StationInfo(
                id=station_id,
                name=station['title'],
                coordinate=Coordinate(
                    latitude=station['latitude'], longitude=station['longitude']
                ),
                zoom_level=_zoom_level_conversion(
                    float(station['zoomLevel']) if 'zoomLevel' in station else None
                ),
            )
    return stations


def list_stations() -> List[StationInfo]:
    """List ARSO weather stations."""
    return list(get_arso_stations().values())


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get ARSO map layers."""
    url: str = MAP_URL.get(map_type, '')
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown map type',
        )

    url = join_url(API_BASEURL, url, trailing_slash=True)
    print(url)

    async with AsyncClient() as client:
        response = await client.get(url)

    country_suffix = f'?country={CountryID.Slovenia}'

    layers: List[MapLayer] = []
    bbox: List[float] = []
    for layer in response.json():
        if map_type == MapType.WeatherCondition:
            if 'nowcast' in layer['path']:
                url = layer['path'].replace(
                    '/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json',
                    '/stations/map/current',
                )
            else:
                url = layer['path'].replace(
                    '/uploads/probase/www/fproduct/json/sl/forecast_si_',
                    '/stations/map/',
                )
                url = url.replace('.json', '')
            url += country_suffix
        else:
            url = join_url(BASEURL, layer['path'])
        time = datetime.strptime(layer['valid'], '%Y-%m-%dT%H:%M:%S%z')
        layers.append(
            MapLayer(
                url=url,
                timestamp=str(int(time.timestamp())) + '000',
                observation=ObservationType.Historical
                if layer['mode'] == 'ANL'
                else ObservationType.Forecast,
            )
        )

        if not bbox and 'bbox' in layer:
            bbox = [float(b) for b in layer['bbox'].split(',')]

    for i in range(1, len(layers)):
        if layers[i].observation != layers[i - 1].observation:
            layers[i - 1].observation = ObservationType.Recent
            break

        if i == len(layers) - 1:
            layers[i].observation = ObservationType.Recent

    return layers, bbox


def _parse_feature(
    feature: Dict[Any, Any], observation: ObservationType
) -> Tuple[StationInfo, WeatherCondition]:
    properties = feature['properties']

    feature_id = properties['id'].strip('_')
    title = properties['title']
    timeline = properties['days'][0]['timeline'][0]
    time = datetime.strptime(timeline['valid'], '%Y-%m-%dT%H:%M:%S%z')
    icon = timeline['clouds_icon_wwsyn_icon']

    if 'txsyn' in timeline:
        temperature: float = float(timeline['txsyn'])
        temperature_low: Optional[float] = float(timeline['tnsyn'])
    else:
        temperature = float(timeline['t'])
        temperature_low = None

    geometry = feature['geometry']
    coordinate = Coordinate(
        latitude=float(geometry['coordinates'][1]),
        longitude=float(geometry['coordinates'][0]),
    )

    zoom_level = _zoom_level_conversion(
        float(properties['zoomLevel']) if 'zoomLevel' in properties else None
    )

    station = StationInfo(
        id=feature_id, name=title, coordinate=coordinate, zoom_level=zoom_level
    )

    condition = WeatherCondition(
        observation=observation,
        timestamp=str(int(time.timestamp())) + '000',
        icon=icon,
        temperature=temperature,
    )
    if temperature_low:
        condition.temperature_low = temperature_low

    return (station, condition)


async def get_weather_map(id: str) -> List[WeatherInfo]:
    """Get weather map from ID."""
    url: str = _weather_map_url(id)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    print(url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'features' not in response_body:
        return []

    conditions_list = []
    for feature in response_body['features']:
        station, condition = _parse_feature(
            feature,
            ObservationType.Recent if id == 'current' else ObservationType.Forecast,
        )
        conditions_list.append(WeatherInfo(station=station, condition=condition))

    return conditions_list


async def find_station(query: StationSearchModel) -> List[ExtendedStationInfo]:
    """Get weather information by coordinate or string."""
    url: str = join_url(API_BASEURL, 'locations', trailing_slash=True)

    if query.string and (query.latitude or query.longitude):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )
    elif query.string:
        single = False
        url += f'?loc={query.string}'
    elif query.latitude is not None and query.longitude is not None:
        single = True
        url += f'?lat={query.latitude}&lon={query.longitude}'
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )

    print(url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    locations = []
    if single:
        station, condition = _parse_feature(response_body, ObservationType.Recent)
        return [ExtendedStationInfo.from_station(station, condition)]
    else:
        if 'features' not in response_body:
            return []

        for feature in response_body['features']:
            station, condition = _parse_feature(feature, ObservationType.Recent)
            locations.append(ExtendedStationInfo.from_station(station, condition))

        return locations


__all__ = ['get_map_layers', 'get_weather_map', 'find_station']
