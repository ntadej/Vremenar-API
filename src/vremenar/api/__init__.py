"""Weather API."""

from .version import router as version
from .location import router as location
from .maps import router as maps
from .weather_map import router as weather_map

__all__ = ['version', 'location', 'maps', 'weather_map']
