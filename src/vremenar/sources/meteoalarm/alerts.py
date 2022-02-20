"""MeteoAlarm alerts."""
from deta import Deta  # type: ignore
from fastapi import HTTPException, status
from functools import lru_cache
from typing import Optional

from .utils import get_areas, get_station_area_mappings
from ...definitions import CountryID, LanguageID
from ...models.alerts import AlertAreaWithPolygon, AlertInfo, AlertInfoExtended
from ...utils import logger

deta = Deta()


async def list_alerts(
    country: CountryID, language: LanguageID
) -> list[AlertInfoExtended]:
    """Get alerts for a specific country."""
    db_alerts = deta.AsyncBase(f'{country.full_name()}_meteoalarm_alerts')

    areas: dict[str, AlertAreaWithPolygon] = get_areas(country)
    alerts: list[AlertInfoExtended] = []

    try:
        last_item = None
        total_count = 0
        while True:
            result = await db_alerts.fetch(last=last_item)
            total_count += result.count
            for item in result.items:
                alerts.append(AlertInfoExtended.init(item, language, areas))
            if not result.last:
                break
            last_item = result.last

        logger.debug('Read %s alerts from the database', total_count)
    finally:
        await db_alerts.close()

    return alerts


async def list_alerts_for_critera(
    country: CountryID,
    language: LanguageID = LanguageID.English,
    stations: Optional[list[str]] = None,
    areas: Optional[list[str]] = None,
) -> list[AlertInfo]:
    """Get list of alerts for criteria."""
    if not stations and not areas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='At least one station or area required',
        )

    areas_to_query: list[str] = []
    if areas:
        areas_list = get_areas(country)
        for a in areas:
            if a not in areas_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Unknown alert area',
                )
            areas_to_query.append(a)

    if stations:
        mappings = get_station_area_mappings(country)
        for s in stations:
            if s not in mappings:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Unknown station',
                )
            areas_to_query.append(mappings[s])

    # get unique alert IDs
    db_areas = deta.AsyncBase(f'{country.full_name()}_meteoalarm_areas')
    alert_ids: set[str] = set()
    try:
        for area in areas_to_query:
            item = await db_areas.get(area)
            for id in item['alerts']:
                alert_ids.add(id)
    finally:
        await db_areas.close()

    # get alert info
    alerts: list[AlertInfo] = []
    if alert_ids:
        db_alerts = deta.AsyncBase(f'{country.full_name()}_meteoalarm_alerts')
        try:
            for id in alert_ids:
                item = await db_alerts.get(id)
                alerts.append(AlertInfoExtended.init(item, language).base())
        finally:
            await db_alerts.close()

    # sort the output by time
    alerts = sorted(alerts, key=lambda a: a.onset)

    return alerts


@lru_cache
def list_alert_areas(country: CountryID) -> list[AlertAreaWithPolygon]:
    """Get alert areas for a specific country."""
    return list(get_areas(country).values())
