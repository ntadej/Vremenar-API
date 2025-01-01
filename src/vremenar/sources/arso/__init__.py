"""ARSO weather source."""

from .maps import (
    get_all_map_legends,
    get_map_layers,
    get_map_legend,
    get_supported_map_types,
    get_weather_map,
)
from .stations import (
    current_station_condition,
    find_station,
    list_stations,
)

ARSO_NAME = "Slovenian Environment Agency"
ARSO_URL = "https://meteo.arso.gov.si"

__all__ = [
    "ARSO_NAME",
    "ARSO_URL",
    "current_station_condition",
    "find_station",
    "get_all_map_legends",
    "get_map_layers",
    "get_map_legend",
    "get_supported_map_types",
    "get_weather_map",
    "list_stations",
]
