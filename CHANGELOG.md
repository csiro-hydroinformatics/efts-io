# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.6.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.6.0) - 2025-10-20

<small>[Compare with 0.5.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.5.0...0.6.0)</small>

### Features

- support larger integer for station identifiers, up to 18 or 19 digits or so. ([11dc9e5](https://github.com/csiro-hydroinformatics/efts-io/commit/11dc9e55fb883dbb591a7757dd7548a511762612) by J-M).

## [0.5.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.5.0) - 2025-10-16

<small>[Compare with 0.4.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.4.0...0.5.0)</small>

### Features

- Gracefully handle data with dimensions less than 4 if the missing ones are degenerate (lengh 1). ([abd17b9](https://github.com/csiro-hydroinformatics/efts-io/commit/abd17b9924bbbc23328b27a38eda2517eac876be) by J-M).

### Bug Fixes

- data arrays created from EftsDataset methods should be wirteable to STF2 ([b6b248d](https://github.com/csiro-hydroinformatics/efts-io/commit/b6b248d837be5553904f256a71e1521e199af4f1) by J-M).
- feature for #14 not called early enough when saving to file ([80c6ec9](https://github.com/csiro-hydroinformatics/efts-io/commit/80c6ec97a910d988da510b59ac6428fb42037085) by J-M).

## [0.4.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.4.0) - 2025-07-24

<small>[Compare with 0.3.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.3.0...0.4.0)</small>

### Features

- first revised read-write STF 2.0 round-trip, using low-level netCDF4 bindings ([efb4508](https://github.com/csiro-hydroinformatics/efts-io/commit/efb4508d52fdf8ebd28ba2c5cc74eb862711896f) by J-M).

## [0.3.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.3.0) - 2025-07-21

<small>Bump version to supersede deprecated package version</small>

### Features

- No new feature, version change to supersede a [deprecated package version 0.2](https://pypi.org/project/efts-io/0.2/)

## [0.1.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.1.0) - 2025-07-21

<small>[Compare with first commit](https://github.com/csiro-hydroinformatics/efts-io/compare/4481803cae41eb7f0315c97a864f1d0c7751d4d8...0.1.0)</small>

### Features

- initial implementation of the `save_to_stf2` method to save data in STF2 format. Thanks to [Dr Durga Lal Shrestha](https://people.csiro.au/s/d/durgalal-shrestha) and the Streamflow Forecasting team for providing the starting point of the implementation.
- include sample data in the package ([9c3fcbd](https://github.com/csiro-hydroinformatics/efts-io/commit/9c3fcbdac3f336634700463f70c4985de2f9a940) by J-M).

### Bug Fixes

- likely bug in writing the long name of a simulated variable ([4bd0106](https://github.com/csiro-hydroinformatics/efts-io/commit/4bd010600fc83dc1287e0c457e941d33909d8d71) by J-M).

## [0.0.1](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.0.1) - 2024-08-29

<small>[Compare with first commit](https://github.com/csiro-hydroinformatics/efts-io/compare/4481803cae41eb7f0315c97a864f1d0c7751d4d8...0.0.1)</small>
