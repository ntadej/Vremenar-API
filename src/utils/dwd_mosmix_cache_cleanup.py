#!/usr/bin/env python3

"""DWD MOSMIX cache cleanup."""

from datetime import datetime
from pathlib import Path

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'


def dwd_mosmix_cleanup() -> None:
    """Cleanup DWD MOSMIX data."""
    now = datetime.utcnow()
    for path in DWD_CACHE_DIR.glob('MOSMIX*.json'):
        name = path.name.replace('MOSMIX:', '').strip('.json')
        date = datetime.strptime(name, '%Y-%m-%dT%H:%M:%SZ')
        delta = date - now

        if delta.days < -1:
            print(path.name)
            path.unlink()


if __name__ == '__main__':
    DWD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dwd_mosmix_cleanup()
