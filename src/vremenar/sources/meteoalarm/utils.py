"""MeteoAlarm utils."""
from functools import lru_cache
from json import load
from pathlib import Path

from ...definitions import CountryID
from ...models.alerts import AlertAreaWithPolygon


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
def get_station_area_mappings(country: CountryID) -> dict[str, str]:
    """Get station mappings with alert areas."""
    path: Path = Path.cwd() / f'data/alerts/{country.full_name()}_stations.json'
    mappings: dict[str, str] = {}
    with open(path) as file:
        mappings = load(file)
    return mappings
