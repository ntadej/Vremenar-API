"""LibreWXR weather source."""

from .maps import (
    get_all_map_legends,
    get_global_map_cloud_infrared,
    get_global_map_precipitation,
    get_map_layers,
    get_map_legend,
    get_supported_map_types,
)

LIBREWXR_NAME = "LibreWXR"
LIBREWXR_URL = "https://www.librewxr.com"

get_librewxr_map_legend = get_map_legend

__all__ = [
    "LIBREWXR_NAME",
    "LIBREWXR_URL",
    "get_all_map_legends",
    "get_global_map_cloud_infrared",
    "get_global_map_precipitation",
    "get_librewxr_map_legend",
    "get_map_layers",
    "get_map_legend",
    "get_supported_map_types",
]
