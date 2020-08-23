"""DWD weather source."""

from datetime import datetime, timedelta
from httpx import AsyncClient
from typing import List, Tuple

from ..definitions import ObservationType
from ..models.maps import MapLayer, MapType

MAPS_BASEURL = 'https://maps.dwd.de/geoserver/dwd/ows?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true'  # noqa E501


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get DWD map layers."""
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

    layers: List[MapLayer] = []
    # historical data + recent
    for i in range(18, -1, -1):
        time = current_time - timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:RX-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(
                url,
                str(int(time.timestamp())) + '000',
                ObservationType.Historical if i != 0 else ObservationType.Recent,
            )
        )
    # forecast
    for i in range(1, 19, 1):
        time = current_time + timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:FX-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(url, str(int(time.timestamp())) + '000', ObservationType.Forecast)
        )

    return layers, []


__all__ = ['get_map_layers']
