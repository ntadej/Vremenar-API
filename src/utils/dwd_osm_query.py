#!/usr/bin/env python3

"""DWD get MOSMIX stations."""

import httpx
from json import dump, load
from pathlib import Path
from time import sleep

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'
OSM_CACHE_DIR: Path = Path.cwd() / '.cache/osm'
OSM_URL = 'https://nominatim.openstreetmap.org'

OSM_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load stations list
with open(DWD_CACHE_DIR / 'stations_list.json', 'r') as file:
    stations = load(file)

# Loop over stations
for station_id, station in stations.items():
    print(station_id, station)

    lat = station['lat']
    lon = station['lon']

    reverse_cache = OSM_CACHE_DIR / f'DWD:{station_id}:reverse.json'
    details_cache = OSM_CACHE_DIR / f'DWD:{station_id}:reverse_details.json'

    if not reverse_cache.is_file():
        sleep(1)

        reverse_url = f'{OSM_URL}/reverse.php?lat={lat}&lon={lon}&zoom=16&format=jsonv2'
        print(reverse_url)
        response = httpx.get(reverse_url)
        reverse_result = response.json()

        with open(reverse_cache, 'w') as file:
            dump(reverse_result, file)

        print(f'{reverse_cache} written')
    else:
        print(f'{reverse_cache} exists')
        with open(reverse_cache, 'r') as file:
            reverse_result = load(file)

    if 'error' in reverse_result:
        print()
        continue

    osm_id = reverse_result['osm_id']
    osm_type = reverse_result['osm_type'][0].upper()

    if not details_cache.is_file():
        sleep(1)

        details_url = f'{OSM_URL}/details.php?osmtype={osm_type}&osmid={osm_id}'
        details_url += '&addressdetails=1&format=json'
        print(details_url)
        response = httpx.get(details_url)
        details_result = response.json()

        with open(details_cache, 'w') as file:
            dump(details_result, file)

        print(f'{details_cache} written')
    else:
        print(f'{details_cache} exists')

    print()
