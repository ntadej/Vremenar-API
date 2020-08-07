"""ARSO weather source."""

from datetime import datetime
from httpx import AsyncClient
from typing import List, Optional, Tuple

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

    county_suffix = f'?county={CountryID.Slovenia}'

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
            url = url + county_suffix
        else:
            url = join_url(BASEURL, layer['path'])
        time = datetime.strptime(layer['valid'], '%Y-%m-%dT%H:%M:%S%z')
        layers.append(
            MapLayer(
                url, str(int(time.timestamp())) + '000', ObservationType.Historical
            )
        )

        if not bbox and 'bbox' in layer:
            bbox = [float(b) for b in layer['bbox'].split(',')]

    return layers, bbox


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

        zoom_level: float = float(properties['zoomLevel'])
        zoom_epsilon = 0.25

        zoom_level = zoom_level + 1 if zoom_level == 5 else zoom_level
        zoom_level /= 6
        zoom_level *= 11 - 7.5 - zoom_epsilon
        zoom_level = 11 - zoom_level - zoom_epsilon

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

        conditions_list.append(info)

    return conditions_list


__all__ = ['get_map_layers', 'get_weather_map']
