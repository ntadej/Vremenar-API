"""Weather API."""

from .version import router as version
from .stations import router as stations
from .maps import router as maps
from .copyright import router as copyright

__all__ = ['version', 'stations', 'maps', 'copyright']
