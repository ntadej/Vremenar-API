"""MET.no weather source."""

from .stations import (
    current_station_condition,
    find_station,
)

METNO_NAME = "MET.no"
METNO_URL = "https://www.met.no"

__all__ = [
    "METNO_NAME",
    "METNO_URL",
    "current_station_condition",
    "find_station",
]
