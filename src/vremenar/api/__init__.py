"""Weather API."""

from .version import router as version
from .stations import router as stations
from .maps import router as maps

__all__ = ['version', 'stations', 'maps']
