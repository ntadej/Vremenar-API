# Vremenar API

[![Homepage][web-img]][web] [![Latest release][release-img]][release]
[![License][license-img]][license]
[![Continuous Integration][ci-img]][ci]
[![codecov.io][codecov-img]][codecov] [![CodeFactor][codefactor-img]][codefactor]
[![pre-commit][pre-commit-img]][pre-commit]

A simple API server for [ARSO](https://meteo.arso.gov.si)
and [DWD](https://dwd.de/EN/) weather data.

## Installation and running

Vremenar API is python-based, with Python 3.11 as the minimum supported version.

### Python PDM

This project uses [PDM](https://pdm.fming.dev) to track dependencies.
For basic setup run

```shell
pdm sync
```

### Production running

Gunicorn is recommended and tested in production workflows.
An example command is:

```shell
pdm run start
```

It is recommended to run the API behind a caching server such
as `varnish` as none of the requests are cached by default.

### Development running

Uvicorn can be used directly for development:

```shell
pdm run dev
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

Copyright (C) 2020-2023 Tadej Novak

This project may be used under the terms of the
GNU Affero General Public License version 3.0 as published by the
Free Software Foundation and appearing in the file [LICENSE](LICENSE).

[web]: https://vremenar.app
[release]: https://github.com/ntadej/Vremenar-API/releases/latest
[license]: https://github.com/ntadej/Vremenar-API/blob/main/LICENSE
[ci]: https://github.com/ntadej/Vremenar-API/actions
[codecov]: https://codecov.io/github/ntadej/Vremenar-API?branch=main
[codefactor]: https://www.codefactor.io/repository/github/ntadej/vremenar-api
[pre-commit]: https://results.pre-commit.ci/latest/github/ntadej/Vremenar-API/main
[web-img]: https://img.shields.io/badge/web-vremenar.app-yellow.svg
[release-img]: https://img.shields.io/github/release/ntadej/Vremenar-API.svg
[license-img]: https://img.shields.io/github/license/ntadej/Vremenar-API.svg
[ci-img]: https://github.com/ntadej/Vremenar-API/workflows/Continuous%20Integration/badge.svg
[codecov-img]: https://codecov.io/github/ntadej/Vremenar-API/coverage.svg?branch=main
[codefactor-img]: https://www.codefactor.io/repository/github/ntadej/vremenar-api/badge
[pre-commit-img]: https://results.pre-commit.ci/badge/github/ntadej/Vremenar-API/main.svg
