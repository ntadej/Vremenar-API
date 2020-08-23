"""Weather sources wrapper."""

from typing import List, Optional, Tuple

from ..definitions import CountryID
from ..models.maps import MapLayer, MapType
from ..models.weather import WeatherInfo

from . import arso
from . import dwd


async def get_map_layers(
    country: CountryID, map_type: MapType
) -> Tuple[List[MapLayer], List[float]]:
    """Get map layers for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_map_layers(map_type)
    if country == CountryID.Germany:
        return await dwd.get_map_layers(map_type)

    raise RuntimeError('Unsupported country')


async def get_weather_map(country: CountryID, id: str) -> List[WeatherInfo]:
    """Get weather condition map for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_weather_map(id)

    raise RuntimeError('Unsupported country')


async def find_location(
    country: CountryID,
    string: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> List[WeatherInfo]:
    """Get weather information by coordinate or string."""
    if country == CountryID.Slovenia:
        return await arso.find_location(string, latitude, longitude)

    raise RuntimeError('Unsupported country')
