#!/usr/bin/env python3

"""DWD MOSMIX cache cleanup."""

from datetime import datetime
from pathlib import Path

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'


def dwd_mosmix_cleanup() -> None:
    """Cleanup DWD MOSMIX data."""
    now = datetime.now()
    for path in DWD_CACHE_DIR.glob('MOSMIX*.json'):
        date = datetime.strptime(path.name, 'MOSMIX:%Y-%m-%dT%H:%M:%S.json')
        delta = date - now

        if delta.days < -1:
            print(path.name)
            path.unlink()


if __name__ == '__main__':
    DWD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dwd_mosmix_cleanup()
