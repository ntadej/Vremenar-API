# Vremenar API

[![Homepage][web-img]][web] [![Latest release][release-img]][release]
[![License][license-img]][license]
[![Continuous Integration][ci-img]][ci]
[![codecov.io][codecov-img]][codecov] [![CodeFactor][codefactor-img]][codefactor]

A simple API server for [ARSO](https://meteo.arso.gov.si)
and [DWD](https://dwd.de/EN/) weather data.

## Installation and running

Vremenar API is python-based, with Python 3.11 as the minimum supported version.

### uv

This project uses [uv](https://github.com/astral-sh/uv) to track dependencies.
For basic development setup run

```shell
uv sync
```

For production setup run

```shell
uv sync --no-dev
```

### Production running

To be updated.

### Development running

A simple development CLI using uvicorn can be used directly for development:

```shell
uv run vremenar
```

## Contributing

### pre-commit checks

This project uses `prek`. To setup, run

```shell
prek install
```

To check all files run

```shell
prek run --all
```

## Copyright info

Copyright (C) 2020-2026 Tadej Novak

This project may be used under the terms of the
GNU Affero General Public License version 3.0 as published by the
Free Software Foundation and appearing in the file [LICENSE](LICENSE).

[web]: https://vremenar.app
[release]: https://github.com/ntadej/Vremenar-API/releases/latest
[license]: https://github.com/ntadej/Vremenar-API/blob/main/LICENSE
[ci]: https://github.com/ntadej/Vremenar-API/actions
[codecov]: https://codecov.io/github/ntadej/Vremenar-API?branch=main
[codefactor]: https://www.codefactor.io/repository/github/ntadej/vremenar-api
[web-img]: https://img.shields.io/badge/web-vremenar.app-yellow.svg
[release-img]: https://img.shields.io/github/release/ntadej/Vremenar-API.svg
[license-img]: https://img.shields.io/github/license/ntadej/Vremenar-API.svg
[ci-img]: https://github.com/ntadej/Vremenar-API/workflows/Continuous%20Integration/badge.svg
[codecov-img]: https://codecov.io/github/ntadej/Vremenar-API/coverage.svg?branch=main
[codefactor-img]: https://www.codefactor.io/repository/github/ntadej/vremenar-api/badge
