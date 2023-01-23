"""Weather stations API."""

from fastapi import APIRouter

from .config import defaults
from ..definitions import CountryID
from ..models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ..models.weather import WeatherInfo, WeatherInfoExtended
from ..sources import (
    current_station_condition,
    find_station,
    get_weather_map,
    list_stations,
)

router = APIRouter()


@router.get(
    "/stations/list",
    tags=["stations"],
    name="List stations",
    response_description="List of weather stations",
    **defaults,
)
async def stations_list(
    country: CountryID, extended: bool = False
) -> list[StationInfo] | list[StationInfoExtended]:
    """List weather stations."""
    if extended:
        return await list_stations(country)

    return [s.info() for s in await list_stations(country)]


@router.post(
    "/stations/find",
    tags=["stations"],
    name="Find stations",
    response_description="List of weather stations",
    **defaults,
)
async def find(
    country: CountryID, query: StationSearchModel, include_forecast_only: bool = False
) -> list[StationInfo]:
    """Find weather station."""
    return await find_station(country, query, include_forecast_only)


@router.get(
    "/stations/condition/{station_id}",
    tags=["stations"],
    name="Current station condition",
    response_description="Current weather condition for the chosen station",
    **defaults,
)
async def condition(
    country: CountryID, station_id: str, extended: bool = False
) -> WeatherInfoExtended | WeatherInfo:
    """Get current station condition."""
    condition = await current_station_condition(country, station_id)

    if extended:
        return condition

    return condition.base()


@router.get(
    "/stations/map/{map_id}",
    tags=["stations"],
    name="Weather conditions map",
    response_description="List of weather information",
    **defaults,
)
async def conditions_map(
    country: CountryID, map_id: str, extended: bool = True
) -> list[WeatherInfo] | list[WeatherInfoExtended]:
    """Get weather conditions map for a specific ID."""
    weather_map = await get_weather_map(country, map_id)

    if extended:
        return weather_map

    return [condition.base() for condition in weather_map]
