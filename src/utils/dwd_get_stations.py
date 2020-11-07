#!/usr/bin/env python3

"""DWD get MOSMIX stations."""

from json import dump, load
from pathlib import Path

DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'

file_name = None
for f in DWD_CACHE_DIR.glob('MOSMIX*.json'):
    file_name = f
    break

if not file_name:
    raise RuntimeError('no cached file found')

print(file_name)

with open(file_name, 'r') as file:
    data = load(file)

stations = {}
dwd_map = {}
wmo_map = {}
dwd_set = set()
wmo_set = set()
for r in data:
    dwd_station_id = r['dwd_station_id']
    wmo_station_id = r['wmo_station_id']
    station_id = wmo_station_id

    dwd_set.add(dwd_station_id)
    wmo_set.add(wmo_station_id)

    name = r['station_name']
    if name == 'SWIS-PUNKT':
        continue

    lat = r['lat']
    lon = r['lon']

    stations[station_id] = {
        'name': name,
        'lat': lat,
        'lon': lon,
        'DWD': dwd_station_id,
        'WMO': wmo_station_id,
    }

    wmo_map[wmo_station_id] = dwd_station_id
    if dwd_station_id:
        dwd_map[dwd_station_id] = wmo_station_id

print(len(stations.keys()))

overlap = list(dwd_set.intersection(wmo_set))

file_out = DWD_CACHE_DIR / 'stations_list.json'
print(file_out)
with open(file_out, 'w') as file:
    dump(stations, file, indent=4)

file_out = DWD_CACHE_DIR / 'stations_ID_map.json'
print(file_out)
with open(file_out, 'w') as file:
    dump({'DWD': dwd_map, 'WMO': wmo_map, 'overlap': overlap}, file, indent=4)
