#!/usr/bin/env python3

"""DWD MOSMIX downloader."""

import re
from brightsky.parsers import Parser, wmo_id_to_dwd  # type: ignore
from csv import reader
from datetime import datetime
from dateutil import parser
from json import dumps
from lxml.etree import iterparse, Element, QName  # type: ignore
from pathlib import Path
from typing import Any, Dict, Generator, List, TextIO, cast

DwdRecord = Dict[str, Any]
DwdGenerator = Generator[DwdRecord, None, None]

BRIGHTSKY_CACHE: Path = Path.cwd() / '.cache/brightsky/MOSMIX_S_LATEST_240.kml'
DWD_CACHE_DIR: Path = Path.cwd() / '.cache/dwd'
NS = {
    'dwd': 'https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd',
    'kml': 'http://www.opengis.net/kml/2.2',
}


class MOSMIXParserFast(Parser):  # type: ignore
    """Custom MOSMIX parser for low memory."""

    DEFAULT_URL = BRIGHTSKY_CACHE
    PRIORITY = 20

    ELEMENTS = {
        'DD': 'wind_direction',
        'FF': 'wind_speed',
        'FX1': 'wind_gust_speed',
        'N': 'cloud_cover',
        'PPPP': 'pressure_msl',
        'RR1c': 'precipitation',
        'SunD1': 'sunshine',
        'Td': 'dew_point',
        'TTT': 'temperature',
        'VV': 'visibility',
        'ww': 'condition',
    }

    def parse(self) -> DwdGenerator:
        """Parse the file."""
        self.logger.info('Parsing %s', self.path)

        with open(self.path, 'rb') as file:
            timestamps = []
            source = ''
            for _, elem in iterparse(file):
                tag = QName(elem.tag).localname

                if tag == 'ProductID':
                    source += elem.text + ':'
                    elem.clear()
                elif tag == 'IssueTime':
                    source += elem.text
                    elem.clear()
                elif tag == 'ForecastTimeSteps':
                    timestamps = [
                        parser.parse(r.text)
                        for r in elem.findall('dwd:TimeStep', namespaces=NS)
                    ]
                    elem.clear()

                    print('Got %d timestamps for source %s' % (len(timestamps), source))
                elif tag == 'Placemark':
                    records = self._parse_station(elem, timestamps, source)
                    elem.clear()
                    yield from self._sanitize_records(records)
        pass

    def _parse_station(
        self, station_elem: Element, timestamps: List[datetime], source: str
    ) -> DwdGenerator:
        wmo_station_id = station_elem.find('./kml:name', namespaces=NS).text
        dwd_station_id = wmo_id_to_dwd(wmo_station_id)
        station_name = station_elem.find('./kml:description', namespaces=NS).text
        try:
            lon, lat, height = station_elem.find(
                './kml:Point/kml:coordinates', namespaces=NS
            ).text.split(',')
        except AttributeError:
            self.logger.warning(
                "Ignoring station without coordinates, WMO ID '%s', DWD ID "
                "'%s', name '%s'",
                wmo_station_id,
                dwd_station_id,
                station_name,
            )
            return cast(DwdGenerator, [])
        records: Dict[str, Any] = {'timestamp': timestamps}
        for element, column in self.ELEMENTS.items():
            values_str = station_elem.find(
                f'./*/dwd:Forecast[@dwd:elementName="{element}"]/dwd:value',
                namespaces=NS,
            ).text
            converter = getattr(self, f'parse_{column}', float)
            records[column] = [
                None if row[0] == '-' else converter(row[0])
                for row in reader(re.sub(r'\s+', '\n', values_str.strip()).splitlines())
            ]
            assert len(records[column]) == len(timestamps)
        base_record = {
            'observation_type': 'forecast',
            'source': source,
            'lat': float(lat),
            'lon': float(lon),
            'height': float(height),
            'dwd_station_id': dwd_station_id,
            'wmo_station_id': wmo_station_id,
            'station_name': station_name,
        }
        # Turn dict of lists into list of dicts
        return (
            {**base_record, **dict(zip(records, row))} for row in zip(*records.values())
        )

    def _sanitize_records(self, records: DwdGenerator) -> DwdGenerator:
        for r in records:
            if r['precipitation'] and r['precipitation'] < 0:
                self.logger.warning('Ignoring negative precipitation value: %s', r)
                r['precipitation'] = None
            if r['wind_direction'] and r['wind_direction'] > 360:
                self.logger.warning('Fixing out-of-bounds wind direction: %s', r)
                r['wind_direction'] -= 360
            yield r


def dwd_out(date: datetime) -> str:
    """Get MOSMIX cache file name."""
    return date.strftime('MOSMIX:%Y-%m-%dT%H:%M:%S')


def dwd_open_file(source: str) -> TextIO:
    """Open cache file."""
    file = open(DWD_CACHE_DIR / f'{source}.json', 'w')
    print('[', file=file)
    return file


def dwd_close_file(file: TextIO) -> None:
    """Close cache file."""
    print(']', file=file)
    file.close()


def dwd_mosmix() -> None:
    """Cache DWD MOSMIX data."""
    data: Dict[str, TextIO] = {}

    parser = MOSMIXParserFast()
    # parser.download()  # Not necessary if you supply a local path
    for record in parser.parse():
        source: str = dwd_out(record['timestamp'])
        record['timestamp'] = str(int(record['timestamp'].timestamp())) + '000'
        if source not in data:
            data[source] = dwd_open_file(source)
            data[source].write(dumps(record))
        else:
            data[source].write(f',\n{dumps(record)}')
    # parser.cleanup()  # If you wish to delete any downloaded files

    for _, file in data.items():
        dwd_close_file(file)


if __name__ == '__main__':
    DWD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    dwd_mosmix()
