#!/usr/bin/env python3

"""DWD MOSMIX downloader."""

from brightsky.parsers import MOSMIXParser  # type: ignore
from datetime import datetime
from json import dump
from pathlib import Path
from typing import Any, Dict, List

DwdRecord = Dict[str, Any]

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'


def dwd_out(date: datetime) -> str:
    """Get MOSMIX cache file name."""
    return date.strftime('MOSMIX:%Y-%m-%dT%H:%M:%S')


def dwd_mosmix() -> None:
    """Cache DWD MOSMIX data."""
    data: Dict[str, List[DwdRecord]] = {}

    parser = MOSMIXParser()
    parser.download()  # Not necessary if you supply a local path
    for record in parser.parse():
        source: str = dwd_out(record['timestamp'])
        record['timestamp'] = str(int(record['timestamp'].timestamp())) + '000'
        if source not in data:
            data[source] = []
        data[source].append(record)
    parser.cleanup()  # If you wish to delete any downloaded files

    for source in data:
        with open(DWD_CACHE_DIR / f'{source}.json', 'w') as file:
            dump(data[source], file)


if __name__ == '__main__':
    DWD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dwd_mosmix()
