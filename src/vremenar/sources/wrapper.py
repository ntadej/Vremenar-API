"""Weather sources wrapper."""

from typing import List, Tuple

from ..definitions import CountryID
from ..models.maps import MapLayer, MapType
from ..models.weather import WeatherInfo

from . import arso


async def get_map_layers(
    country: CountryID, map_type: MapType
) -> Tuple[List[MapLayer], List[float]]:
    """Get map layers for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_map_layers(map_type)

    raise RuntimeError('Unsupported country')


async def get_weather_map(country: CountryID, id: str) -> List[WeatherInfo]:
    """Get weather condition map for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_weather_map(id)

    raise RuntimeError('Unsupported country')
