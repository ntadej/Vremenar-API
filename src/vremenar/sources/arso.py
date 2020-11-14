"""ARSO weather source."""

from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from json import load
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import MapLayer, MapType
from ..models.stations import StationInfo, StationSearchModel
from ..models.weather import WeatherCondition, WeatherInfo
from ..utils import join_url, logger, parse_time, to_timestamp

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
    with open(path) as file:
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
    logger.debug('ARSO URL: %s', url)

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
        time = parse_time(layer['valid'])
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
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
    feature: Dict[Any, Any], observation: ObservationType, station_only: bool = False
) -> Tuple[StationInfo, Optional[WeatherCondition]]:
    properties = feature['properties']

    feature_id = properties['id'].strip('_')
    title = properties['title']

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

    if station_only:
        return station, None

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


async def get_weather_map(id: str) -> List[WeatherInfo]:
    """Get weather map from ID."""
    url: str = _weather_map_url(id)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    logger.debug('ARSO URL: %s', url)

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


async def find_station(query: StationSearchModel) -> List[StationInfo]:
    """Find station by coordinate or string."""
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

    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    locations = []
    if single:
        station, _ = _parse_feature(response_body, ObservationType.Recent, True)
        return [station]
    else:
        if 'features' not in response_body:
            return []

        for feature in response_body['features']:
            station, _ = _parse_feature(feature, ObservationType.Recent, True)
            locations.append(station)

        return locations


async def current_station_condition(station_id: str) -> WeatherInfo:
    """Get current station weather condition."""
    stations = get_arso_stations()
    station: Optional[StationInfo] = stations.get(station_id, None)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    url = (
        join_url(API_BASEURL, 'locations', trailing_slash=True) + f'?loc={station.name}'
    )

    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'features' not in response_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    for feature in response_body['features']:
        station, condition = _parse_feature(feature, ObservationType.Recent)
        return WeatherInfo(station=station, condition=condition)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unknown station',
    )


__all__ = [
    'current_station_condition',
    'find_station',
    'get_map_layers',
    'get_weather_map',
]
