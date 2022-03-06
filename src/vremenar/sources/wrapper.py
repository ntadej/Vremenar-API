"""Weather sources wrapper."""

from fastapi import HTTPException, status
from typing import Optional

from ..definitions import CountryID, LanguageID
from ..models.alerts import AlertAreaWithPolygon, AlertInfo
from ..models.maps import MapLayer, MapLegend, MapType, SupportedMapType
from ..models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ..models.weather import WeatherInfoExtended

from . import arso
from . import dwd
from . import meteoalarm


def get_all_supported_map_types(country: CountryID) -> list[SupportedMapType]:
    """Get supported map types for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_supported_map_types()
    if country == CountryID.Germany:
        return dwd.get_supported_map_types()

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def get_map_layers(
    country: CountryID, map_type: MapType
) -> tuple[list[MapLayer], list[float]]:
    """Get map layers for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_map_layers(map_type)
    if country == CountryID.Germany:
        return await dwd.get_map_layers(map_type)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


def get_all_map_legends(country: CountryID) -> list[MapLegend]:
    """Get all map legends for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_all_map_legends()
    if country == CountryID.Germany:
        return dwd.get_all_map_legends()

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


def get_map_legend(country: CountryID, map_type: MapType) -> MapLegend:
    """Get map legend by type for the chosen country."""
    if country == CountryID.Slovenia:
        return arso.get_map_legend(map_type)
    if country == CountryID.Germany:
        return dwd.get_map_legend(map_type)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def get_weather_map(country: CountryID, map_id: str) -> list[WeatherInfoExtended]:
    """Get weather condition map for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.get_weather_map(map_id)
    if country == CountryID.Germany:
        return await dwd.get_weather_map(map_id)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def list_stations(country: CountryID) -> list[StationInfoExtended]:
    """List weather stations for the chosen country."""
    if country == CountryID.Slovenia:
        return await arso.list_stations()
    if country == CountryID.Germany:
        return await dwd.list_stations()

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def find_station(
    country: CountryID, query: StationSearchModel, include_forecast_only: bool
) -> list[StationInfo]:
    """Find weather station by coordinate or string."""
    if country == CountryID.Slovenia:
        return await arso.find_station(query)
    if country == CountryID.Germany:
        return await dwd.find_station(query, include_forecast_only)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def current_station_condition(
    country: CountryID, station_id: str
) -> WeatherInfoExtended:
    """Get current station weather condition."""
    if country == CountryID.Slovenia:
        return await arso.current_station_condition(station_id)
    if country == CountryID.Germany:
        return await dwd.current_station_condition(station_id)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported country',
    )


async def list_alerts(country: CountryID, language: LanguageID) -> list[AlertInfo]:
    """Get list of alerts for a country."""
    return await meteoalarm.list_alerts(country, language)


async def list_alerts_for_critera(
    country: CountryID,
    language: LanguageID = LanguageID.English,
    stations: Optional[list[str]] = None,
    areas: Optional[list[str]] = None,
) -> list[AlertInfo]:
    """Get list of alerts for criteria."""
    return await meteoalarm.list_alerts_for_critera(country, language, stations, areas)


async def list_alert_areas(country: CountryID) -> list[AlertAreaWithPolygon]:
    """Get list of alert areas for a country."""
    return await meteoalarm.list_alert_areas(country)
