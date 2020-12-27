"""Weather sources wrapper."""

from fastapi import HTTPException, status
from typing import List, Tuple

from ..definitions import CountryID
from ..models.maps import MapLayer, MapLegend, MapType, SupportedMapType
from ..models.stations import StationInfo, StationSearchModel
from ..models.weather import WeatherInfo

from . import arso
from . import dwd


def get_all_supported_map_types(country: CountryID) -> List[SupportedMapType]:
    """Get supported map types for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_supported_map_types()
    if country == CountryID.Germany:
        return dwd.get_supported_map_types()

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def get_map_layers(
    country: CountryID, map_type: MapType
) -> Tuple[List[MapLayer], List[float]]:
    """Get map layers for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_map_layers(map_type)
    if country == CountryID.Germany:
        return await dwd.get_map_layers(map_type)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


def get_all_map_legends(country: CountryID) -> List[MapLegend]:
    """Get all map legends for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_all_map_legends()
    if country == CountryID.Germany:
        return dwd.get_all_map_legends()

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


def get_map_legend(country: CountryID, map_type: MapType) -> MapLegend:
    """Get map legend by type for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_map_legend(map_type)
    if country == CountryID.Germany:
        return dwd.get_map_legend(map_type)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def get_weather_map(country: CountryID, id: str) -> List[WeatherInfo]:
    """Get weather condition map for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_weather_map(id)
    if country == CountryID.Germany:
        return await dwd.get_weather_map(id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


def list_stations(country: CountryID) -> List[StationInfo]:
    """List weather stations for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.list_stations()
    if country == CountryID.Germany:
        return dwd.list_stations()

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def find_station(
    country: CountryID, query: StationSearchModel
) -> List[StationInfo]:
    """Find weather station by coordinate or string."""
    if country == CountryID.Slovenia:
        return await arso.find_station(query)
    if country == CountryID.Germany:
        return await dwd.find_station(query)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def current_station_condition(country: CountryID, station_id: str) -> WeatherInfo:
    """Get current station weather condition."""
    if country == CountryID.Slovenia:
        return await arso.current_station_condition(station_id)
    if country == CountryID.Germany:
        return await dwd.current_station_condition(station_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )
