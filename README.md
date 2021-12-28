# Vremenar API

[![Homepage][web-img]][web] [![Latest release][release-img]][release]
[![License][license-img]][license] [![Black][black-img]][black]
[![Continuous Integration][ci-img]][ci]
[![codecov.io][codecov-img]][codecov] [![CodeFactor][codefactor-img]][codefactor]

A simple API server for [ARSO](https://meteo.arso.gov.si)
and [DWD](https://dwd.de/EN/) weather data.

## Installation and running

Vremenar API is python-based, with Python 3.9 as the minimum supported version.

### Python Poetry

This project uses [Python Poetry](https://python-poetry.org) to track dependencies.
For basic setup run

```shell
poetry install
```

### Production running

Gunicorn is recommended and tested in production workflows.
An example command is:

```shell
poetry run gunicorn vremenar.main:app -w 2 -k vremenar.worker.ConfigurableWorker
```

It is recommended to run the API behind a caching server such
as `varnish` as none of the requests are cached by default.

### Development running

Uvicorn can be used directly for development:

```shell
poetry run uvicorn vremenar.main:app --reload --reload-dir src/vremenar --log-level debug
```

## Contributing

### pre-commit

This project uses `pre-commit`. To setup, run

```shell
pre-commit install
```

To check all files run

```shell
pre-commit run --all
```

## Copyright info

Copyright (C) 2020-2021 Tadej Novak

This project may be used under the terms of the
GNU Affero General Public License version 3.0 as published by the
Free Software Foundation and appearing in the file [LICENSE](LICENSE).

[web]: https://vremenar.tano.si
[release]: https://github.com/ntadej/Vremenar-API/releases/latest
[license]: https://github.com/ntadej/Vremenar-API/blob/master/LICENSE
[ci]: https://github.com/ntadej/Vremenar-API/actions
[black]: https://github.com/psf/black
[codecov]: https://codecov.io/github/ntadej/Vremenar-API?branch=master
[codefactor]: https://www.codefactor.io/repository/github/ntadej/vremenar-api
[web-img]: https://img.shields.io/badge/web-vremenar.tano.si-yellow.svg
[release-img]: https://img.shields.io/github/release/ntadej/Vremenar-API.svg
[license-img]: https://img.shields.io/github/license/ntadej/Vremenar-API.svg
[ci-img]: https://github.com/ntadej/Vremenar-API/workflows/Continuous%20Integration/badge.svg
[black-img]: https://img.shields.io/badge/code%20style-black-000000.svg
[codecov-img]: https://codecov.io/github/ntadej/Vremenar-API/coverage.svg?branch=master
[codefactor-img]: https://www.codefactor.io/repository/github/ntadej/vremenar-api/badge
