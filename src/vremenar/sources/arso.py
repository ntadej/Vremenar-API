"""ARSO weather source."""

from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from json import load
from pathlib import Path
from typing import Any, Optional

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import (
    MapLayer,
    MapLegend,
    MapLegendItem,
    MapRenderingType,
    MapType,
    SupportedMapType,
)
from ..models.stations import (
    StationInfo,
    StationInfoExtended,
    StationSearchModel,
)
from ..models.weather import WeatherCondition, WeatherInfoExtended
from ..utils import join_url, logger, parse_time, to_timestamp

BASEURL: str = 'https://vreme.arso.gov.si'
API_BASEURL: str = 'https://vreme.arso.gov.si/api/1.0/'
TIMEOUT: int = 15

MAP_URL = {
    MapType.WeatherCondition: '/forecast_si_data/',
    MapType.Precipitation: '/inca_precip_data/',
    MapType.CloudCoverage: '/inca_cloud_data/',
    MapType.WindSpeed: '/inca_wind_data/',
    MapType.Temperature: '/inca_t2m_data/',
    MapType.HailProbability: '/inca_hail_data/',
}


def get_supported_map_types() -> list[SupportedMapType]:
    """Get ARSO supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.WeatherCondition, rendering_type=MapRenderingType.Icons
        ),
        SupportedMapType(
            map_type=MapType.Precipitation,
            rendering_type=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.CloudCoverage, rendering_type=MapRenderingType.Image
        ),
        SupportedMapType(
            map_type=MapType.WindSpeed,
            rendering_type=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.Temperature,
            rendering_type=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.HailProbability,
            rendering_type=MapRenderingType.Image,
            has_legend=True,
        ),
    ]


def _zoom_level_conversion(zoom_level: Optional[float]) -> Optional[float]:
    if zoom_level is not None:
        zoom_level = zoom_level + 1.0 if zoom_level == 5.0 else zoom_level
        zoom_level /= 6
        zoom_epsilon = 0.25
        zoom_level *= 11 - 7.5 - zoom_epsilon
        zoom_level = 11 - zoom_level - zoom_epsilon
        return zoom_level
    return None


def _weather_map_url(map_id: str) -> str:
    if map_id == 'current':
        return f'{BASEURL}/uploads/probase/www/fproduct/json/sl/nowcast_si_latest.json'

    if map_id[0] == 'd':
        return (
            f'{BASEURL}/uploads/probase/www/fproduct/json/sl/forecast_si_{map_id}.json'
        )

    return ''


@lru_cache
def get_arso_stations() -> dict[str, StationInfoExtended]:
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
                zoom_level=_zoom_level_conversion(
                    float(station['zoomLevel']) if 'zoomLevel' in station else None
                ),
            )
    return {k: v for k, v in sorted(stations.items(), key=lambda item: item[1].name)}


@lru_cache
def list_stations() -> list[StationInfoExtended]:
    """List ARSO weather stations."""
    return list(get_arso_stations().values())


async def get_map_layers(map_type: MapType) -> tuple[list[MapLayer], list[float]]:
    """Get ARSO map layers."""
    url: str = MAP_URL.get(map_type, '')
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unsupported or unknown map type',
        )

    url = join_url(API_BASEURL, url, trailing_slash=True)
    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url, timeout=TIMEOUT)

    country_suffix = f'?country={CountryID.Slovenia}'

    layers: list[MapLayer] = []
    bbox: list[float] = []
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


def get_map_legend(map_type: MapType) -> MapLegend:
    """Get ARSO map legend."""
    if map_type == MapType.Precipitation:
        items = []
        items.append(MapLegendItem(value='', color='transparent', placeholder=True))
        items.append(MapLegendItem(value='0', color='transparent'))
        items.append(MapLegendItem(value='15', color='#3e67ff'))
        items.append(MapLegendItem(value='18', color='#3797ff'))
        items.append(MapLegendItem(value='21', color='#30c1f6'))
        items.append(MapLegendItem(value='24', color='#31e7fc'))
        items.append(MapLegendItem(value='27', color='#33d397'))
        items.append(MapLegendItem(value='30', color='#2fef28'))
        items.append(MapLegendItem(value='33', color='#8bfa36'))
        items.append(MapLegendItem(value='36', color='#c8fa33'))
        items.append(MapLegendItem(value='39', color='#f6fb2a'))
        items.append(MapLegendItem(value='42', color='#fed430'))
        items.append(MapLegendItem(value='45', color='#ff9a2c'))
        items.append(MapLegendItem(value='48', color='#fe6637'))
        items.append(MapLegendItem(value='51', color='#d42e38'))
        items.append(MapLegendItem(value='54', color='#b22923'))
        items.append(MapLegendItem(value='57', color='#d436d7'))
        items.append(MapLegendItem(value='dBZ', color='transparent', placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.WindSpeed:
        items = []
        items.append(MapLegendItem(value='', color='transparent', placeholder=True))
        items.append(MapLegendItem(value='0', color='transparent'))
        items.append(MapLegendItem(value='10', color='#09609680'))
        items.append(MapLegendItem(value='20', color='#096'))
        items.append(MapLegendItem(value='30', color='#96c'))
        items.append(MapLegendItem(value='40', color='#e54cff'))
        items.append(MapLegendItem(value='50', color='#f09'))
        items.append(MapLegendItem(value='60', color='#e51919'))
        items.append(MapLegendItem(value='70', color='#933'))
        items.append(MapLegendItem(value='80', color='#4c3333'))
        items.append(MapLegendItem(value='90', color='#630'))
        items.append(MapLegendItem(value='100', color='#963'))
        items.append(MapLegendItem(value='110', color='#b29966'))
        items.append(MapLegendItem(value='km/h', color='transparent', placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.Temperature:
        items = []
        items.append(MapLegendItem(value='', color='transparent', placeholder=True))
        items.append(MapLegendItem(value='-22', color='#fff'))
        items.append(MapLegendItem(value='-20', color='#e1e1e1'))
        items.append(MapLegendItem(value='-18', color='#bebebe'))
        items.append(MapLegendItem(value='-16', color='#828282'))
        items.append(MapLegendItem(value='-14', color='#565474'))
        items.append(MapLegendItem(value='-12', color='#59447f'))
        items.append(MapLegendItem(value='-10', color='#47007f'))
        items.append(MapLegendItem(value='-8', color='#32007f'))
        items.append(MapLegendItem(value='-6', color='#0000ac'))
        items.append(MapLegendItem(value='-4', color='#0000f0'))
        items.append(MapLegendItem(value='-2', color='#2059e7'))
        items.append(MapLegendItem(value='0', color='#007eff'))
        items.append(MapLegendItem(value='2', color='#00beff'))
        items.append(MapLegendItem(value='4', color='#aff'))
        items.append(MapLegendItem(value='6', color='#01f7c6'))
        items.append(MapLegendItem(value='8', color='#18d78c'))
        items.append(MapLegendItem(value='10', color='#00aa64'))
        items.append(MapLegendItem(value='12', color='#2baa2b'))
        items.append(MapLegendItem(value='14', color='#2bc82b'))
        items.append(MapLegendItem(value='16', color='#01ff00'))
        items.append(MapLegendItem(value='18', color='#cf0'))
        items.append(MapLegendItem(value='20', color='#ff0'))
        items.append(MapLegendItem(value='22', color='#eded7e'))
        items.append(MapLegendItem(value='24', color='#e4cc66'))
        items.append(MapLegendItem(value='26', color='#dcae49'))
        items.append(MapLegendItem(value='28', color='#fa0'))
        items.append(MapLegendItem(value='30', color='#f50'))
        items.append(MapLegendItem(value='32', color='red'))
        items.append(MapLegendItem(value='34', color='#c80000'))
        items.append(MapLegendItem(value='36', color='#780000'))
        items.append(MapLegendItem(value='38', color='#640000'))
        items.append(MapLegendItem(value='40', color='#500000'))
        items.append(MapLegendItem(value='°C', color='transparent', placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.HailProbability:
        items = []
        items.append(MapLegendItem(value='', color='transparent', placeholder=True))
        items.append(MapLegendItem(value='', color='transparent'))
        items.append(MapLegendItem(value='low', color='#fae100', translatable=True))
        items.append(
            MapLegendItem(value='moderate', color='#fa7d00', translatable=True)
        )
        items.append(MapLegendItem(value='large', color='#fa0000', translatable=True))
        items.append(
            MapLegendItem(
                value='probability',
                color='transparent',
                translatable=True,
                placeholder=True,
            )
        )
        return MapLegend(map_type=map_type, items=items)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported or unknown map type',
    )


def get_all_map_legends() -> list[MapLegend]:
    """Get all ARSO map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]


def _parse_station(feature: dict[Any, Any]) -> Optional[StationInfoExtended]:
    stations = get_arso_stations()

    properties = feature['properties']

    station_id = properties['id'].strip('_')
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        return None

    return station


def _parse_feature(
    feature: dict[Any, Any], observation: ObservationType
) -> tuple[Optional[StationInfoExtended], Optional[WeatherCondition]]:
    stations = get_arso_stations()

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


async def get_weather_map(map_id: str) -> list[WeatherInfoExtended]:
    """Get weather map from ID."""
    url: str = _weather_map_url(map_id)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    response_body = response.json()
    if 'features' not in response_body:
        return []

    conditions_list = []
    for feature in response_body['features']:
        station, condition = _parse_feature(
            feature,
            ObservationType.Recent if map_id == 'current' else ObservationType.Forecast,
        )
        if station and condition:
            conditions_list.append(
                WeatherInfoExtended(station=station, condition=condition)
            )

    return conditions_list


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(API_BASEURL, 'locations', trailing_slash=True)

    if query.string and (query.latitude or query.longitude):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )

    if query.string:
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
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()

    if single:
        station = _parse_station(response_body)
        if station:
            return [station]

    if 'features' not in response_body:
        return []

    locations: list[StationInfo] = []
    for feature in response_body['features']:
        station = _parse_station(feature)
        if station:
            locations.append(station)

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = get_arso_stations()
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
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
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()
    if 'features' not in response_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    for feature in response_body['features']:
        _, condition = _parse_feature(feature, ObservationType.Recent)
        return WeatherInfoExtended(station=station, condition=condition)

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
