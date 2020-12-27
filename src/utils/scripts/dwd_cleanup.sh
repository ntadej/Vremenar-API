#!/bin/bash

source src/utils/.venv/bin/activate

nice src/utils/dwd_mosmix_cache_cleanup.py

deactivate
