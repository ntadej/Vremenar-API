"""Weather alerts API."""
from fastapi import APIRouter, Query

from vremenar.definitions import CountryID, LanguageID
from vremenar.models.alerts import AlertAreaWithPolygon, AlertInfo
from vremenar.sources import list_alert_areas, list_alerts, list_alerts_for_critera

from .config import defaults

router = APIRouter()

default_query = Query(None)


@router.get(
    "/alerts/areas",
    tags=["alerts"],
    name="List weather alert areas",
    response_description="List of weather alert areas for a country",
    **defaults,
)
async def areas_list(country: CountryID) -> list[AlertAreaWithPolygon]:
    """List weather alert areas for a country."""
    return await list_alert_areas(country)


@router.get(
    "/alerts/list",
    tags=["alerts"],
    name="List weather alerts",
    response_description="List of weather alerts",
    **defaults,
)
async def alerts_list(
    country: CountryID,
    language: LanguageID = LanguageID.English,
    station: list[str] | None = default_query,
    area: list[str] | None = default_query,
) -> list[AlertInfo]:
    """List weather alerts for the criteria."""
    return await list_alerts_for_critera(country, language, station, area)


@router.get(
    "/alerts/full_list",
    tags=["alerts"],
    name="List all weather alerts",
    response_description="List of all weather alerts for a country",
    **defaults,
)
async def alerts_full_list(
    country: CountryID,
    language: LanguageID = LanguageID.English,
) -> list[AlertInfo]:
    """List weather alerts for a country."""
    return await list_alerts(country, language)
