# efts-io

[![ci](https://github.com/csiro-hydroinformatics/efts-io/workflows/ci/badge.svg)](https://github.com/csiro-hydroinformatics/efts-io/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-mkdocs-708FCC.svg?style=flat)](https://csiro-hydroinformatics.github.io/efts-io/)
[![pypi version](https://img.shields.io/pypi/v/efts-io.svg)](https://pypi.org/project/efts-io/)
<!-- [![gitpod](https://img.shields.io/badge/gitpod-workspace-708FCC.svg?style=flat)](https://gitpod.io/#https://github.com/csiro-hydroinformatics/efts-io)
[![gitter](https://badges.gitter.im/join%20chat.svg)](https://app.gitter.im/#/room/#efts-io:gitter.im) -->

## Overview

Plain text files are not well suited to storing the large volumes of data generated for and by ensemble streamflow forecasts with numerical weather prediction models. netCDF is a binary file format developed primarily for climate, ocean and meteorological data. netCDF has traditionally been used to store time slices of gridded data, rather than complete time series of point data. **efts-io** is for handling the latter. It reads and writes netCDF data following the [NetCDF for Water Forecasting Conventions v2.0](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting).

## Installation

With `pip`:

```bash
pip install efts-io
```

<!-- With [`pipx`](https://github.com/pipxproject/pipx):

```bash
python -m pip install --user pipx
pipx install efts-io
``` -->

## Development workflow

See [contributing.md](./contributing.md) if you want to contribute. This project follows practices from a template and the page [copier-uv: Working on a project](https://pawamoy.github.io/copier-uv/work). Many thanks to [Timothée Mazzucotelli](https://pawamoy.github.io/) for sharing this template.

## LLM context files

Using LLMs for development is a best practice way to get started and explore. While LLMs **cannot code for you**, they can be helpful assistants. You must check, refactor, test, and vet any code any LLM generates for you - but they are helpful productivity tools. The following files will be useful as context for LLMs to build modelling workflows with the **efts-io** package.

<!-- - [llms.txt](https://csiro-hydroinformatics.github.io/swift-py-doc/llms.txt): Links to what is included
- [llms-ctx.txt](https://csiro-hydroinformatics.github.io/swift-py-doc/llms-ctx.txt): Programming API pages -->

The following links should work from the [online HTML documentation](https://csiro-hydroinformatics.github.io/efts-io/) (but may not from README.md):

- [llms.txt](./llms.txt): Links to what is included
- [llms-ctx.txt](./llms-ctx.txt): Programming API pages

These files follow the proposed [/llms.txt standard](https://llmstxt.org), and are produced with [mkdocs-llmstxt](https://pawamoy.github.io/mkdocs-llmstxt/).

