"""Weather API."""

from .maps import router as maps
from .weather_map import router as weather_map

__all__ = ['maps', 'weather_map']
