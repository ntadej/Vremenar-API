"""RainViewer weather source."""

from .maps import (
    get_all_map_legends,
    get_global_map_cloud_infrared,
    get_global_map_precipitation,
    get_map_layers,
    get_map_legend,
    get_supported_map_types,
)

get_rainviewer_map_legend = get_map_legend

__all__ = [
    "get_global_map_cloud_infrared",
    "get_global_map_precipitation",
    "get_map_layers",
    "get_map_legend",
    "get_all_map_legends",
    "get_rainviewer_map_legend",
    "get_supported_map_types",
]
