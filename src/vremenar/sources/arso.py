"""ARSO weather source."""

from datetime import datetime
from httpx import AsyncClient
from typing import List, Tuple

from ..definitions import ObservationType
from ..models.maps import MapLayer, MapType
from ..utils import join_url

BASEURL: str = 'https://vreme.arso.gov.si'
API_BASEURL: str = 'https://vreme.arso.gov.si/api/1.0/'

MAP_URL = {
    MapType.Precipitation: '/inca_precip_data/',
    MapType.CloudCoverage: '/inca_cloud_data/',
    MapType.WindSpeed: '/inca_wind_data/',
    MapType.Temperature: '/inca_t2m_data/',
    MapType.HailProbability: '/inca_hail_data/',
}


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get ARSO map layers."""
    url: str = MAP_URL.get(map_type, '')
    if not url:
        raise RuntimeError('Unknown map type')

    url = join_url(API_BASEURL, url, trailing_slash=True)
    print(url)

    async with AsyncClient() as client:
        response = await client.get(url)

    layers: List[MapLayer] = []
    bbox: List[float] = []
    for layer in response.json():
        url = join_url(BASEURL, layer['path'])
        time = datetime.strptime(layer['valid'], '%Y-%m-%dT%H:%M:%S%z')
        layers.append(
            MapLayer(
                url, str(int(time.timestamp())) + '000', ObservationType.Historical
            )
        )

        if not bbox:
            bbox = [float(b) for b in layer['bbox'].split(',')]

    return layers, bbox


__all__ = ['get_map_layers']
