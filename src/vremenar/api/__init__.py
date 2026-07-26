"""Weather API."""

from .alerts import router as alerts
from .copyright import router as copyright  # ruff: ignore[builtin-import-shadowing]
from .maps import router as maps
from .stations import router as stations
from .version import router as version

__all__ = [
    "alerts",
    "copyright",
    "maps",
    "stations",
    "version",
]
