"""MeteoAlarm alerts."""
from deta import Deta  # type: ignore
from functools import lru_cache
from json import load
from pathlib import Path

from ...definitions import CountryID, LanguageID
from ...models.alerts import AlertAreaWithPolygon, AlertInfoExtended
from ...utils import logger

deta = Deta()


async def list_alerts(
    country: CountryID, language: LanguageID
) -> list[AlertInfoExtended]:
    """Get alerts for a specific country."""
    db = deta.AsyncBase(f'{country.full_name()}_meteoalarm_alerts')

    areas: dict[str, AlertAreaWithPolygon] = get_areas(country)
    alerts: list[AlertInfoExtended] = []

    try:
        last_item = None
        total_count = 0
        while True:
            result = await db.fetch(last=last_item)
            total_count += result.count
            for item in result.items:
                alerts.append(AlertInfoExtended.init(item, language, areas))
            if not result.last:
                break
            last_item = result.last

        logger.debug('Read %s alerts from the database', total_count)
    finally:
        await db.close()

    return alerts


@lru_cache
def get_areas(country: CountryID) -> dict[str, AlertAreaWithPolygon]:
    """Get alert areas dictionary."""
    path: Path = Path.cwd() / f'data/alerts/{country.full_name()}.json'
    areas: dict[str, AlertAreaWithPolygon] = {}
    with open(path) as file:
        data = load(file)
        for area in data:
            id: str = area['code']
            areas[id] = AlertAreaWithPolygon(
                id=id, name=area['name'], polygons=area['polygons']
            )
    return {k: v for k, v in sorted(areas.items(), key=lambda item: item[1].id)}


@lru_cache
def list_alert_areas(country: CountryID) -> list[AlertAreaWithPolygon]:
    """Get alert areas for a specific country."""
    return list(get_areas(country).values())
