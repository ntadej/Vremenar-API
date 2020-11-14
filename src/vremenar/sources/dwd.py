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
from ..models.maps import MapLayer, MapType
from ..models.stations import StationInfo, StationSearchModel
from ..models.weather import WeatherCondition, WeatherInfo
from ..units import kelvin_to_celsius
from ..utils import day_or_night, join_url, logger, parse_time, to_timestamp

CACHE_PATH: Path = Path.cwd() / '.cache/dwd'
BRIGHTSKY_BASEURL = 'https://api.brightsky.dev'
MAPS_BASEURL = 'https://maps.dwd.de/geoserver/dwd/ows?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true'  # noqa E501


def _zoom_level_conversion(location_type: str, admin_level: float) -> float:
    # location_type: {'city', 'town', 'village', 'suburb', 'hamlet', 'isolated',
    #                 'airport', 'special' }
    # admin_level: {'4', '6', '8', '9', '10'}

    if admin_level >= 10:
        return 10.35
    elif admin_level >= 9:
        return 9.9
    elif admin_level >= 8:
        if location_type in ['town']:
            return 8.5
        elif location_type in ['village', 'suburb']:
            return 9.1
        else:
            return 9.5
    elif admin_level >= 6:
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
    else:
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
def get_dwd_stations() -> Dict[str, StationInfo]:
    """Get a dictionary of supported DWD stations."""
    path: Path = Path.cwd() / 'data/stations/DWD.csv'
    stations: Dict[str, StationInfo] = {}
    with open(path, newline='') as csvfile:
        csv = reader(csvfile, dialect='excel')
        next(csv)  # Skip header row.
        for row in csv:
            station_id: str = row[0]
            stations[station_id] = StationInfo(
                id=station_id,
                name=row[3],
                coordinate=Coordinate(latitude=row[4], longitude=row[5]),
                zoom_level=_zoom_level_conversion(row[6], float(row[7])),
                metadata={'DWD_ID': row[1]},
            )
    return stations


def list_stations() -> List[StationInfo]:
    """List DWD weather stations."""
    return list(get_dwd_stations().values())


async def get_map_layers(map_type: MapType) -> Tuple[List[MapLayer], List[float]]:
    """Get DWD map layers."""
    layers: List[MapLayer] = []

    if map_type == MapType.WeatherCondition:
        country_suffix = f'?country={CountryID.Germany}'

        url = '/stations/map/current'
        url += country_suffix
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(datetime.now()),
                observation=ObservationType.Recent,
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


def _weather_map_url(id: str) -> Path:
    paths = sorted(list(CACHE_PATH.glob('MOSMIX*.json')))
    now = datetime.utcnow()
    now = now.replace(tzinfo=timezone.utc)
    for path in paths:
        name = path.name.replace('MOSMIX:', '').strip('.json')
        date = parse_time(name)
        delta = (date - now).total_seconds()

        if delta < 0:
            continue

        return path
    return paths[0]


def _parse_record(
    record: Dict[str, Any], observation: ObservationType
) -> Tuple[Optional[StationInfo], Optional[WeatherCondition]]:
    station_id = record['wmo_station_id']
    stations = get_dwd_stations()

    if station_id not in stations:
        return (None, None)

    station = stations[station_id]

    condition = WeatherCondition(
        observation=observation,
        timestamp=record['timestamp'],
        icon=_get_icon(station, record, parse_time(record['time'])),
        temperature=kelvin_to_celsius(record['temperature']),
    )

    return (station, condition)


async def get_weather_map(id: str) -> List[WeatherInfo]:
    """Get weather map from ID."""
    path: Path = _weather_map_url(id)
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
            ObservationType.Recent if id == 'current' else ObservationType.Forecast,
        )
        if not station:
            continue
        conditions_list.append(WeatherInfo(station=station, condition=condition))

    return conditions_list


def _parse_source(source: Dict[str, Any]) -> StationInfo:
    stations = get_dwd_stations()
    source_id = source['wmo_station_id']
    if source_id in stations:
        temp_station = stations[source_id]
        return StationInfo(
            id=temp_station.id,
            name=temp_station.name,
            coordinate=temp_station.coordinate,
        )

    return StationInfo(
        id=source_id,
        name=source['station_name'],
        coordinate=Coordinate(latitude=source['lat'], longitude=source['lon']),
    )


async def find_station(query: StationSearchModel) -> List[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)

    if query.string:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only coordinates are required',
        )
    elif query.latitude is not None and query.longitude is not None:
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

    locations = []
    for source in response_body['sources']:
        locations.append(_parse_source(source))

    return locations


async def current_station_condition(station_id: str) -> WeatherInfo:
    """Get current station weather condition."""
    stations = get_dwd_stations()
    station: Optional[StationInfo] = stations.get(station_id, None)
    # TODO: enable validation once all stations are in
    # if not station:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail='Unknown station',
    #     )

    url: str = (
        join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)
        + f'?wmo_station_id={station_id}'
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

    return WeatherInfo(station=station, condition=condition)


__all__ = [
    'current_station_condition',
    'find_station',
    'get_map_layers',
    'get_weather_map',
]
