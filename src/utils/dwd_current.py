#!/usr/bin/env python3

"""DWD current weather downloader."""

from brightsky.parsers import CurrentObservationsParser  # type: ignore
from csv import reader
from json import dump
from pathlib import Path
from typing import Any, Dict, List

DwdRecord = Dict[str, Any]
NaN = float('nan')

DWD_STATIONS_CURRENT: Path = Path.cwd() / 'data/stations/DWD.current.csv'
DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'


def dwd_stations() -> List[str]:
    """Get a list of supported DWD stations."""
    stations: List[str] = []
    with open(DWD_STATIONS_CURRENT, newline='') as csvfile:
        csv = reader(csvfile)
        for row in csv:
            stations.append(row[0])
    return stations


def dwd_current() -> None:
    """Cache DWD current weather data."""
    stations: List[str] = dwd_stations()
    records: List[DwdRecord] = []

    for station_id in stations:
        if len(station_id) == 4:
            station_id += '_'
        url = (
            f'https://opendata.dwd.de/weather/weather_reports/poi/{station_id}-BEOB.csv'
        )

        print(url)

        parser = CurrentObservationsParser(url=url)
        parser.download()
        for record in parser.parse(lat=NaN, lon=NaN, height=NaN, station_name=''):
            record['time'] = record['timestamp'].strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
            record['timestamp'] = str(int(record['timestamp'].timestamp())) + '000'
            records.append(record)
            break
        parser.cleanup()  # If you wish to delete any downloaded files

    with open(DWD_CACHE_DIR / 'CURRENT.json', 'w') as file:
        dump(records, file)


if __name__ == '__main__':
    DWD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dwd_current()
