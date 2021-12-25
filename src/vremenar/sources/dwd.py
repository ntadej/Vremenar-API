"""DWD weather source."""

from csv import reader
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from json import load
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..definitions import CountryID, ObservationType
from ..models.common import Coordinate
from ..models.maps import (
    MapLayer,
    MapLegend,
    MapLegendItem,
    MapRenderingType,
    MapType,
    SupportedMapType,
)
from ..models.stations import (
    StationBase,
    StationInfo,
    StationInfoExtended,
    StationSearchModel,
)
from ..models.weather import WeatherCondition, WeatherInfoExtended
from ..units import kelvin_to_celsius
from ..utils import (
    day_or_night,
    join_url,
    logger,
    parse_time,
    parse_timestamp,
    to_timestamp,
)

CACHE_PATH: Path = Path.cwd() / '.cache/dwd'
BRIGHTSKY_BASEURL = 'https://api.brightsky.dev'
MAPS_BASEURL = 'https://maps.dwd.de/geoserver/dwd/ows?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true'  # noqa E501


def get_supported_map_types() -> List[SupportedMapType]:
    """Get DWD supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.WeatherCondition, rendering_type=MapRenderingType.Icons
        ),
        SupportedMapType(
            map_type=MapType.Precipitation,
            rendering_type=MapRenderingType.Tiles,
            has_legend=True,
        ),
    ]


def _zoom_level_conversion(location_type: str, admin_level: float) -> float:
    # location_type: {'city', 'town', 'village', 'suburb', 'hamlet', 'isolated',
    #                 'airport', 'special' }
    # admin_level: {'4', '6', '8', '9', '10'}
    if admin_level >= 10:
        return 10.35
    if admin_level >= 9:
        return 9.9
    if admin_level >= 8:
        if location_type in ['town']:
            return 8.5
        if location_type in ['village', 'suburb']:
            return 9.1
        return 9.5
    if admin_level >= 6:
        return 7.8
    return 7.5


def _get_icon(station: StationInfo, weather: Dict[str, Any], time: datetime) -> str:
    # SOURCE:
    # conditions: dry, fog, rain, sleet, snow, hail, thunderstorm, null
    #
    # ICONS:
    # time: day/night
    # base: FG, clear, overcast, partCloudy, prevCloudy
    # intensity: light, mod, heavy
    # modifiers: DZ (drizzle), FG (fog), RA (rain), RASN (rain+snow), SN (snow),
    #            SHGR (hail shower), SHRA (rain shower),
    #            SHRASN (rain+snow shower), SHSN (snow shower),
    #            TS (thunderstorm), TSGR(hail thunderstorm), TSRA (rain thunderstorm),
    #            TSRASN(rain+snow thunderstorm), TSSN (snow thunderstorm)
    #
    # CRITERIA:
    # rain:
    #   light - when the precipitation rate is < 2.5 mm per hour
    #   moderate - when the precipitation rate is between 2.5 mm and 10 mm per hour
    #   heavy - when the precipitation rate is > 10 mm per hour
    # sky:
    #   clear - 0 to 1/8
    #   partly cloudy - 1/8 to
    #   mostly cloudy -
    #   overcast -

    time_of_day = day_or_night(station.coordinate, time)
    base_icon = 'clear'
    condition = None
    if weather['condition'] == 'fog':  # TODO: intensity
        base_icon = 'FG'
    elif 'cloud_cover' in weather and weather['cloud_cover'] is not None:
        cloud_cover_fraction = weather['cloud_cover'] / 100
        if 1 / 8 <= cloud_cover_fraction < 4 / 8:
            base_icon = 'partCloudy'
        elif 4 / 8 <= cloud_cover_fraction < 7 / 8:
            base_icon = 'prevCloudy'
        else:
            base_icon = 'overcast'

    precipitation_intensity = (
        weather['precipitation_60']
        if 'precipitation_60' in weather
        else weather['precipitation']
    )
    if precipitation_intensity > 0:  # TODO: snow intensity
        if precipitation_intensity > 10:
            intensity = 'heavy'
        elif precipitation_intensity > 2.5:
            intensity = 'mod'
        else:
            intensity = 'light'

        if weather['condition'] in ['hail', 'sleet']:
            precipitation_type = 'SHGR'
        elif weather['condition'] == 'thunderstorm':
            precipitation_type = 'TSRA'
        elif weather['condition'] == 'snow':
            precipitation_type = 'SN'
        else:
            precipitation_type = 'RA'

        condition = f'{intensity}{precipitation_type}'

    if condition:
        return f'{base_icon}_{condition}_{time_of_day}'

    return f'{base_icon}_{time_of_day}'


@lru_cache
def get_dwd_stations() -> Dict[str, StationInfoExtended]:
    """Get a dictionary of supported DWD stations."""
    path: Path = Path.cwd() / 'data/stations/DWD.csv'
    stations: Dict[str, StationInfoExtended] = {}
    with open(path, newline='') as csvfile:
        csv = reader(csvfile, dialect='excel')
        for row in csv:
            station_id: str = row[0]
            stations[station_id] = StationInfoExtended(
                id=station_id,
                name=row[4],
                coordinate=Coordinate(
                    latitude=row[5], longitude=row[6], altitude=row[7]
                ),
                zoom_level=_zoom_level_conversion(row[8], float(row[9])),
                forecast_only=not int(row[2]),
                metadata={'DWD_ID': row[1], 'status': row[10]},
            )
    return {k: v for k, v in sorted(stations.items(), key=lambda item: item[1].name)}


@lru_cache
def list_stations() -> List[StationInfoExtended]:
    """List DWD weather stations."""
    return list(get_dwd_stations().values())


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get DWD map layers."""
    layers: List[MapLayer] = []

    if map_type == MapType.WeatherCondition:
        now = datetime.now(tz=timezone.utc)
        now = now.replace(minute=0, second=0, microsecond=0)

        country_suffix = f'?country={CountryID.Germany}'

        # TODO: proper current
        layers.append(
            MapLayer(
                url=f'/stations/map/current{country_suffix}',
                timestamp=to_timestamp(now),
                observation=ObservationType.Recent,
            )
        )

        # Forecast
        soon = now + timedelta(hours=2)
        soon_string = soon.strftime('%Y-%m-%dT%H:%M:%SZ')
        layers.append(
            MapLayer(
                url=f'/stations/map/{soon_string}{country_suffix}',
                timestamp=to_timestamp(soon),
                observation=ObservationType.Forecast,
            )
        )

        # Today
        start = now.replace(hour=0)
        for i in range(1, 8):
            time = start + timedelta(hours=i * 3)
            if time <= soon:
                continue
            time_string = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            layers.append(
                MapLayer(
                    url=f'/stations/map/{time_string}{country_suffix}',
                    timestamp=to_timestamp(time),
                    observation=ObservationType.Forecast,
                )
            )

        # 7 days
        start = now + timedelta(hours=24 - now.hour)
        for i in range(28):
            time = start + timedelta(hours=i * 6)
            time_string = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            layers.append(
                MapLayer(
                    url=f'/stations/map/{time_string}{country_suffix}',
                    timestamp=to_timestamp(time),
                    observation=ObservationType.Forecast,
                )
            )

        return layers, []

    if map_type != MapType.Precipitation:
        return [], []

    current_time = datetime.utcnow()
    current_now = datetime.now()
    utc_delta = (current_now - current_time).seconds
    time_delta = timedelta(
        minutes=current_time.minute % 5,
        seconds=current_time.second,
        microseconds=current_time.microsecond,
    )
    current_time -= time_delta
    if time_delta.seconds < 100:  # buffer for recent image
        current_time -= timedelta(minutes=5)
    test_time = current_time.isoformat()
    test_url = f'{MAPS_BASEURL}&layers=dwd:RX-Produkt&bbox=5,50,6,51&width=100&height=100&time={test_time}.000Z'  # noqa E501

    logger.debug('DWD Map URL: %s', test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url)

    if 'InvalidDimensionValue' in response.text:
        logger.info('Current map not available yet')
        current_time -= timedelta(minutes=5)

    # historical data + recent
    for i in range(18, -1, -1):
        time = current_time - timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:RX-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Historical
                if i != 0
                else ObservationType.Recent,
            )
        )
    # forecast
    for i in range(1, 19, 1):
        time = current_time + timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta)
        url = f'{MAPS_BASEURL}&layers=dwd:WN-Produkt&width=512&height=512&time={time_string}.000Z'  # noqa E501
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Forecast,
            )
        )

    return layers, []


def get_map_legend(map_type: MapType) -> MapLegend:
    """Get DWD map legend."""
    if map_type == MapType.Precipitation:
        items = []
        items.append(MapLegendItem(value='', color='transparent', placeholder=True))
        items.append(MapLegendItem(value='0', color='transparent'))
        items.append(MapLegendItem(value='7', color='#97F9FC'))
        items.append(MapLegendItem(value='10', color='#6CF8FC'))
        items.append(MapLegendItem(value='12', color='#58CBCA'))
        items.append(MapLegendItem(value='15', color='#489A36'))
        items.append(MapLegendItem(value='19', color='#5CBF1C'))
        items.append(MapLegendItem(value='24', color='#99CD1B'))
        items.append(MapLegendItem(value='28', color='#CCE628'))
        items.append(MapLegendItem(value='33', color='#FDF734'))
        items.append(MapLegendItem(value='37', color='#F9C432'))
        items.append(MapLegendItem(value='42', color='#F28831'))
        items.append(MapLegendItem(value='46', color='#ED462F'))
        items.append(MapLegendItem(value='51', color='#B53322'))
        items.append(MapLegendItem(value='55', color='#4A4CFB'))
        items.append(MapLegendItem(value='60', color='#173ACA'))
        items.append(MapLegendItem(value='65', color='#9B3C99'))
        items.append(MapLegendItem(value='75', color='#EA64FE'))
        items.append(MapLegendItem(value='85', color='#000000'))
        items.append(MapLegendItem(value='dBZ', color='transparent', placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unsupported or unknown map type',
    )


def get_all_map_legends() -> List[MapLegend]:
    """Get all DWD map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]


def _weather_map_url(map_id: str) -> Optional[Path]:
    paths = sorted(list(CACHE_PATH.glob('MOSMIX*.json')))
    now = datetime.utcnow()
    now = now.replace(tzinfo=timezone.utc)
    for path in paths:
        if map_id == 'current':
            name = path.name.replace('MOSMIX:', '').strip('.json')
            date = parse_time(name)
            delta = (date - now).total_seconds()

            if delta < 0:
                continue

            return path

        if path.name == f'MOSMIX:{map_id}.json':
            return path
    return None


def _parse_record(
    record: Dict[str, Any], observation: ObservationType
) -> Tuple[Optional[StationBase], Optional[WeatherCondition]]:
    station_id = record['wmo_station_id']
    stations = get_dwd_stations()

    if station_id not in stations:
        return None, None

    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        return None, None

    if not station.metadata or station.metadata['status'] != '1':
        return None, None

    condition = WeatherCondition(
        observation=observation,
        timestamp=record['timestamp'],
        icon=_get_icon(station, record, parse_timestamp(record['timestamp'])),
        temperature=kelvin_to_celsius(record['temperature']),
    )

    return station, condition


async def get_weather_map(map_id: str) -> List[WeatherInfoExtended]:
    """Get weather map from ID."""
    path: Optional[Path] = _weather_map_url(map_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Map ID is not recognised',
        )

    logger.debug('DWD cache location: %s', path)

    with open(path) as file:
        records = load(file)

    conditions_list = []
    for record in records:
        station, condition = _parse_record(
            record,
            ObservationType.Recent if map_id == 'current' else ObservationType.Forecast,
        )
        if not station:
            continue
        conditions_list.append(
            WeatherInfoExtended(station=station, condition=condition)
        )

    return conditions_list


def _parse_source(source: Dict[str, Any]) -> Optional[StationInfoExtended]:
    stations = get_dwd_stations()
    source_id = source['wmo_station_id']
    if source_id in stations:
        return stations[source_id]

    return None


async def find_station(query: StationSearchModel) -> List[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)

    if query.string:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only coordinates are required',
        )

    if query.latitude is not None and query.longitude is not None:
        url += f'?lat={query.latitude}&lon={query.longitude}'
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only coordinates are required',
        )

    logger.debug('Brightsky URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'sources' not in response_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    locations: List[StationInfo] = []
    for source in response_body['sources']:
        station = _parse_source(source)
        if station:
            locations.append(station)

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = get_dwd_stations()
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)
    url += f'?lat={station.coordinate.latitude}&lon={station.coordinate.longitude}'

    logger.debug('Brightsky URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'sources' not in response_body:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    for source in response_body['sources']:
        station = _parse_source(source)
        break

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    weather = response_body['weather']

    time = parse_time(weather['timestamp'])

    condition = WeatherCondition(
        observation=ObservationType.Recent,
        timestamp=to_timestamp(time),
        icon=_get_icon(station, weather, time),
        temperature=weather['temperature'],
    )

    return WeatherInfoExtended(station=station, condition=condition)


__all__ = [
    'current_station_condition',
    'find_station',
    'get_map_layers',
    'get_weather_map',
]
