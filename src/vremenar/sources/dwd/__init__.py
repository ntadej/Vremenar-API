"""DWD weather source."""

from .maps import (
    get_all_map_legends,
    get_map_layers,
    get_map_legend,
    get_supported_map_types,
    get_weather_map,
)
from .stations import current_station_condition, find_station, list_stations

DWD_NAME = "Deutscher Wetterdienst"
DWD_URL = "https://dwd.de"

__all__ = [
    "DWD_NAME",
    "DWD_URL",
    "current_station_condition",
    "find_station",
    "get_all_map_legends",
    "get_map_layers",
    "get_map_legend",
    "get_supported_map_types",
    "get_weather_map",
    "list_stations",
]
