#!/usr/bin/env python3

"""DWD get MOSMIX stations summary."""

from csv import writer
from json import load
from pathlib import Path
from typing import Any, Dict

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'
OSM_CACHE_DIR: Path = Path.cwd() / '.cache/osm'

# allowed_types = ['city', 'town', 'village', 'suburb']
allowed_types = ['city', 'town', 'village']

verbose = False

# load stations list
with open(DWD_CACHE_DIR / 'stations_list.json') as file:
    stations_list = load(file)

with open(DWD_CACHE_DIR / 'stations.csv', 'w', newline='') as file_out:
    csv = writer(file_out, delimiter=',')

    stations: Dict[str, Dict[str, Any]] = {}
    count = 1
    skipped = 0
    for station_id, station in stations_list.items():
        if verbose:
            print(count, station_id, station)

        count += 1

        reverse_details = OSM_CACHE_DIR / f'DWD:{station_id}:reverse_details.json'
        if not reverse_details.is_file():
            skipped += 1
            csv.writerow(
                [
                    station_id,
                    station['WMO'],
                    station['DWD'],
                    station['name'],
                    '',
                    station['lat'],
                    station['lon'],
                ]
            )
            if verbose:
                print(f'no reverse details for {station_id}')
                print()
            continue

        with open(reverse_details) as file:
            reverse_info = load(file)

        address = None
        address_hierarchy = reverse_info['address']
        for a in address_hierarchy:
            if a['place_type'] in allowed_types:
                address = a
                break
            if a['class'] == 'place' and a['type'] in allowed_types:
                address = a
                break

        if not address:
            skipped += 1
            csv.writerow(
                [
                    station_id,
                    station['WMO'],
                    station['DWD'],
                    station['name'],
                    '',
                    station['lat'],
                    station['lon'],
                ]
            )
            if verbose:
                print('missing address')
                print()
            continue

        if verbose:
            print(address)

        stype = address['place_type'] if address['place_type'] else address['type']
        stations[station_id] = {
            'name': address['localname'],
            'dwd_name': station['name'],
            'latitude': station['lat'],
            'longitude': station['lon'],
            'type': stype,
            'admin_level': address['admin_level'],
        }
        csv.writerow(
            [
                station_id,
                station['WMO'],
                station['DWD'],
                station['name'],
                address['localname'],
                station['lat'],
                station['lon'],
                stype,
                address['admin_level'],
            ]
        )
        if verbose:
            print(stations[station_id])
            print()

stations_all = len(stations_list)
stations_available = len(stations.keys())
print(f'{stations_available}/{skipped}/{stations_all}')
