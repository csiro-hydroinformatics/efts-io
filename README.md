# efts-io

[![ci](https://github.com/csiro-hydroinformatics/efts-io/workflows/ci/badge.svg)](https://github.com/csiro-hydroinformatics/efts-io/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-zensical-FF9100.svg?style=flat)](https://csiro-hydroinformatics.github.io/efts-io/)
[![pypi version](https://img.shields.io/pypi/v/efts-io.svg)](https://pypi.org/project/efts-io/)
[![gitter](https://img.shields.io/badge/matrix-chat-4DB798.svg?style=flat)](https://app.gitter.im/#/room/#efts-io:gitter.im)

Ensemble forecast time series

## Overview

Plain text files are not well suited to storing the large volumes of data generated for and by ensemble streamflow forecasts with numerical weather prediction models. netCDF is a binary file format developed primarily for climate, ocean and meteorological data. netCDF has traditionally been used to store time slices of gridded data, rather than complete time series of point data. **efts-io** is for handling the latter. It reads and writes netCDF data following the [NetCDF for Water Forecasting Conventions v2.0](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting).

## Installation

```bash
pip install efts-io
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install efts-io
```
