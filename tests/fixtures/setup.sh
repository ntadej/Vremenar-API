#!/bin/bash

if [[ ! -d ".cache/dwd" ]]; then
    current_time=$(date -v+1H -u "+%Y-%m-%dT%H:00:00Z")
    mkdir -p ".cache/dwd"
    cp "tests/fixtures/DWD_MOSMIX.json" ".cache/dwd/MOSMIX:${current_time}.json"
fi
