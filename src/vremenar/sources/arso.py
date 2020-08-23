"""ARSO weather source."""

from datetime import datetime
from fastapi import HTTPException, status
from httpx import AsyncClient
from typing import Any, Dict, List, Optional, Tuple

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import MapLayer, MapType
from ..models.weather import WeatherInfo
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


def _weather_map_url(id: str) -> str:
    if id == 'current':
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json'
    else:
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/forecast_si_{id}.json'


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get ARSO map layers."""
    url: str = MAP_URL.get(map_type, '')
    if not url:
        raise RuntimeError('Unknown map type')

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
                    '/weather_map/current',
                )
            else:
                url = layer['path'].replace(
                    '/uploads/probase/www/fproduct/json/sl/forecast_si_',
                    '/weather_map/',
                )
                url = url.replace('.json', '')
            url += country_suffix
        else:
            url = join_url(BASEURL, layer['path'])
        time = datetime.strptime(layer['valid'], '%Y-%m-%dT%H:%M:%S%z')
        layers.append(
            MapLayer(
                url,
                str(int(time.timestamp())) + '000',
                ObservationType.Historical
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


def _parse_feature(feature: Dict[Any, Any]) -> WeatherInfo:
    properties = feature['properties']

    feature_id = properties['id']
    title = properties['title']
    timeline = properties['days'][0]['timeline'][0]
    observation = ObservationType.Forecast
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
        float(geometry['coordinates'][1]), float(geometry['coordinates'][0])
    )

    if 'zoomLevel' in properties:
        zoom_level: Optional[float] = float(properties['zoomLevel'])
        if zoom_level is not None:
            zoom_level = zoom_level + 1.0 if zoom_level == 5.0 else zoom_level
            zoom_level /= 6
            zoom_epsilon = 0.25
            zoom_level *= 11 - 7.5 - zoom_epsilon
            zoom_level = 11 - zoom_level - zoom_epsilon
    else:
        zoom_level = None

    info = WeatherInfo(
        feature_id,
        observation,
        str(int(time.timestamp())) + '000',
        title,
        icon,
        temperature,
        coordinate,
        zoom_level,
    )
    if temperature_low:
        info.temperature_low = temperature_low

    return info


async def get_weather_map(id: str) -> List[WeatherInfo]:
    """Get weather map from ID."""
    url: str = _weather_map_url(id)
    if not url:
        raise RuntimeError('Unsupported ID')

    print(url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'features' not in response_body:
        return []

    conditions_list = []
    for feature in response_body['features']:
        info = _parse_feature(feature)
        conditions_list.append(info)

    return conditions_list


async def find_location(
    string: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> List[WeatherInfo]:
    """Get weather information by coordinate or string."""
    url: str = join_url(API_BASEURL, 'locations', trailing_slash=True)

    if string and (latitude or longitude):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )
    elif string:
        single = False
        url += f'?loc={string}'
    elif latitude is not None and longitude is not None:
        single = True
        url += f'?lat={latitude}&lon={longitude}'
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
        return [_parse_feature(response_body)]
    else:
        if 'features' not in response_body:
            return []

        for feature in response_body['features']:
            info = _parse_feature(feature)
            locations.append(info)

        return locations


__all__ = ['get_map_layers', 'get_weather_map', 'find_location']
