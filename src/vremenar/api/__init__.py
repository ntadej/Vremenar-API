"""Weather API."""

from .version import router as version
from .stations import router as stations
from .maps import router as maps
from .weather_map import router as weather_map

__all__ = ['version', 'stations', 'maps', 'weather_map']
