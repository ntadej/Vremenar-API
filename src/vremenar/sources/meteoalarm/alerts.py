"""MeteoAlarm alerts."""
from fastapi import HTTPException, status
from json import loads
from typing import Optional

from ...database.redis import redis
from ...database.stations import get_stations
from ...definitions import CountryID, LanguageID
from ...models.alerts import AlertAreaWithPolygon, AlertInfo
from ...utils import chunker, logger


async def list_alerts_areas(country: CountryID) -> dict[str, AlertAreaWithPolygon]:
    """Get alerts areas for a specific country."""
    areas: dict[str, AlertAreaWithPolygon] = {}

    async with redis.client() as connection:
        codes = await connection.smembers(f'alerts_area:{country.value}')
        async with connection.pipeline(transaction=False) as pipeline:
            for code in codes:
                pipeline.hgetall(f'alerts_area:{country.value}:{code}:info')
            response = await pipeline.execute()

        for area in response:
            areas[area['code']] = AlertAreaWithPolygon(
                id=area['code'], name=area['name'], polygons=loads(area['polygons'])
            )

    logger.debug('Read %s alerts areas from the database', len(areas))

    return {k: v for k, v in sorted(areas.items(), key=lambda item: item[1].id)}


async def list_alerts(
    country: CountryID,
    language: LanguageID,
    ids: Optional[set[str]] = None,
    areas: Optional[set[str]] = None,
) -> list[AlertInfo]:
    """Get alerts for a specific country."""
    alerts: list[AlertInfo] = []

    async with redis.client() as connection:
        if ids is None:
            ids = await connection.smembers(f'alert:{country.value}')
        async with connection.pipeline(transaction=False) as pipeline:
            for id in ids:
                pipeline.hgetall(f'alert:{country.value}:{id}:info')
                pipeline.hgetall(
                    f'alert:{country.value}:{id}:localised_{language.value}'
                )
                pipeline.smembers(f'alert:{country.value}:{id}:areas')
            response = await pipeline.execute()

        areas_dict = await list_alerts_areas(country)
        for info, localised, alert_areas in chunker(response, 3):
            if areas is not None:
                alert_areas = {area for area in alert_areas if area in areas}
            alerts.append(AlertInfo.init(info, localised, alert_areas, areas_dict))

    logger.debug('Read %s alerts from the database', len(alerts))

    return alerts


async def list_alert_ids_for_areas(country: CountryID, areas: set[str]) -> set[str]:
    """Get alert IDs for requested areas."""
    async with redis.pipeline() as pipeline:
        for area in areas:
            pipeline.smembers(f'alerts_area:{country.value}:{area}:alerts')
        response = await pipeline.execute()
    return set.union(*response)


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

    areas_to_query: set[str] = set()
    if areas:
        areas_list = await list_alerts_areas(country)
        for a in areas:
            if a not in areas_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Unknown alert area',
                )
            areas_to_query.add(a)

    if stations:
        stations_list = await get_stations(country)
        for s in stations:
            if s not in stations_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Unknown station',
                )
            if (
                stations_list[s].metadata is not None
                and 'alerts_area' in stations_list[s].metadata  # type: ignore
            ):
                areas_to_query.add(
                    stations_list[s].metadata['alerts_area']  # type: ignore
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Station has no assigned alerts area',
                )

    # get unique alert IDs
    alert_ids: set[str] = await list_alert_ids_for_areas(country, areas_to_query)

    # get alert info
    alerts: list[AlertInfo] = await list_alerts(
        country, language, alert_ids, areas_to_query
    )
    # sort the output by time
    alerts = sorted(alerts, key=lambda a: a.onset)

    return alerts


async def list_alert_areas(country: CountryID) -> list[AlertAreaWithPolygon]:
    """Get alert areas for a specific country."""
    areas = await list_alerts_areas(country)
    return list(areas.values())
