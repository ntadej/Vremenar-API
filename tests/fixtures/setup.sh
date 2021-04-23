#!/bin/bash

if [[ ! -d ".cache/dwd" ]]; then
    if [[ $(uname) = "Darwin" ]]; then
        current_time=$(date -v+1H -u "+%Y-%m-%dT%H:00:00Z")
    else
        current_time=$(date -d "+1 hour" -u "+%Y-%m-%dT%H:00:00Z")
    fi
    mkdir -p ".cache/dwd"
    cp "tests/fixtures/DWD_MOSMIX.json" ".cache/dwd/MOSMIX:${current_time}.json"
fi

echo "{}" > version.json
