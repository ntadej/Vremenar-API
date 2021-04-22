#!/bin/bash

mkdir -p ".cache/brightsky"
pushd ".cache/brightsky" || exit 1
wget https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml/MOSMIX_S_LATEST_240.kmz 2>&1
nice 7z x MOSMIX_S_LATEST_240.kmz
rm MOSMIX_S_LATEST_240.kmz
mv MOSMIX* MOSMIX_S_LATEST_240.kml
popd || exit 1

source src/utils/.venv/bin/activate

if ! nice src/utils/dwd_mosmix.py 2>&1; then
    echo "Error running 'dwd_mosmix.py'!" 1>&2
fi

if ! nice src/utils/dwd_current.py 2>&1; then
    echo "Error running 'dwd_current.py'!" 1>&2
fi

deactivate

if [[ -d ".cache/dwd-tmp" ]]; then
    cp ".cache/dwd-tmp/"*.json ".cache/dwd/"
    rm -r ".cache/dwd-tmp"
fi

if [[ -d ".cache/brightsky" ]]; then
    rm -r ".cache/brightsky"
fi
