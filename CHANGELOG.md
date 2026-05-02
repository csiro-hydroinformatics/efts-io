# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


<!-- insertion marker -->
## [0.10.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.10.0) - 2026-05-02

<small>[Compare with 0.9.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.9.0...0.10.0)</small>

### Features

- support lead time dimension; use US spelling 'realization'; apply formatting; fix unit tests.  This is a squash to try to get rid of stupid Mac Format and/or carriage returns that found their way in commit messages like a plague. ([44de2bf](https://github.com/csiro-hydroinformatics/efts-io/commit/44de2bf38fc63bbbe98eabb8c654d6d031f159d7) by J-M).

## [0.9.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.9.0) - 2026-05-02

<small>[Compare with 0.8.1](https://github.com/csiro-hydroinformatics/efts-io/compare/0.8.1...0.9.0)</small>

### Bug Fixes

- markdown had unresolved link that made the CI check-docs fail ([0a3f520](https://github.com/csiro-hydroinformatics/efts-io/commit/0a3f52045eeeaf87b532995bb6ad780d286ada03) by J-M).
### Features

- use the US spelling 'realization' for realisation (in memory array). ([f04f363](https://github.com/csiro-hydroinformatics/efts-io/commit/f04f363e568278208e54eb678b1360880c71fe76) by J-M).
- work in progress to support the lead time dimension; test driven implementation of the I/O. ([e216c8c](https://github.com/csiro-hydroinformatics/efts-io/commit/e216c8ceb5e78b45b5a042159e04be28153e7586) by J-M).

### Code Refactoring

- tackle remaining unit tests failures, overly zealous or checking against STF conventions actually not respected de facto. ([d3cf6f4](https://github.com/csiro-hydroinformatics/efts-io/commit/d3cf6f4dabd8be281ec44a17eae4f07fc1542532) by J-M).

## [0.8.1](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.8.1) - 2026-04-08

<small>[Compare with 0.8.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.8.0...0.8.1)</small>

## [0.8.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.8.0) - 2026-04-08

<small>[Compare with 0.7.1](https://github.com/csiro-hydroinformatics/efts-io/compare/0.7.1...0.8.0)</small>

### Features

- additional functions to create and test metadata attributes as per the STF 2.0 conventions. Relates to #31. ([6b5fe07](https://github.com/csiro-hydroinformatics/efts-io/commit/6b5fe07c41ec92df2a6ffcdaa0c5e9495db65bed) by J-M).
- WIP improve the API to create data attributes adhering to the STF 2.0 conventions. relates to #32. ([65a1286](https://github.com/csiro-hydroinformatics/efts-io/commit/65a1286a983c2c298775d166e56e3a711d8a0d32) by J-M).
- WIP to support utc offset time zones, https://github.com/csiro-hydroinformatics/efts-io/issues/31 ([e0ff4e5](https://github.com/csiro-hydroinformatics/efts-io/commit/e0ff4e51e08f47f10d3c1c2126aaa861759b7fe0) by J-M).

### Bug Fixes

- address issues F and G in #38, legacy paths from R implementation. Just unused so removed. ([3449244](https://github.com/csiro-hydroinformatics/efts-io/commit/34492448a74e64bbcf9b6265fa92e5b92efa70bd) by J-M).
- address multiple STF 2.0 compliance issues, due to various endo/exogenous factors ([a7760f6](https://github.com/csiro-hydroinformatics/efts-io/commit/a7760f67f1003ef75b1c39b6490de2f9975d6108) by J-M).
- potential if improbable bug with array indices ([b28e17c](https://github.com/csiro-hydroinformatics/efts-io/commit/b28e17c5dffcb2ce4d39eee85cced70f2d449114) by J-M).

### Code Refactoring

- low level functions writing to netcdf. Relates to #34. ([ec64390](https://github.com/csiro-hydroinformatics/efts-io/commit/ec64390571c66eeb18efccc13c1e18e213c2f005) by J-M).
- WIP de-uglify the low level write function. ([acc9478](https://github.com/csiro-hydroinformatics/efts-io/commit/acc94787892409955dd25d0d4424d39ac8b5e681) by J-M).
- WIP deprecate StfDataType enum inherited that stemmed from some Matlab/third party python code numeric hard coding ([75d1427](https://github.com/csiro-hydroinformatics/efts-io/commit/75d14275a925403f0a95472983a3401a26c0bde2) by J-M).

## [0.7.1](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.7.1) - 2026-02-24

<small>[Compare with 0.7.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.7.0...0.7.1)</small>

### Bug Fixes

- files with single station_id can now be read. ([5fd3ba4](https://github.com/csiro-hydroinformatics/efts-io/commit/5fd3ba4c546796b9232a4e11c64fb630dcf858e4) by J-M).

## [0.7.0](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.7.0) - 2026-01-21

<small>[Compare with 0.6.4](https://github.com/csiro-hydroinformatics/efts-io/compare/0.6.4...0.7.0)</small>

### Features

- add a  and  methods to EftsDataSet ([9c394a3](https://github.com/csiro-hydroinformatics/efts-io/commit/9c394a3a5cc59512b4807da0f17f22b514203056) by J-M).

### Bug Fixes

- units of the in-memory data were not taken into account when writing to disk. ([a1882a5](https://github.com/csiro-hydroinformatics/efts-io/commit/a1882a57d06e21fb0d0c9f6d78c11ab63bcfc416) by J-M).

## [0.6.4](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.6.4) - 2026-01-21

<small>[Compare with 0.6.3](https://github.com/csiro-hydroinformatics/efts-io/compare/0.6.3...0.6.4)</small>

### Bug Fixes

- units of the in-memory data were not taken into account when writing to disk. ([a1882a5](https://github.com/csiro-hydroinformatics/efts-io/commit/a1882a57d06e21fb0d0c9f6d78c11ab63bcfc416) by J-M).

## [0.6.3](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.6.3) - 2026-01-19

<small>[Compare with 0.6.2](https://github.com/csiro-hydroinformatics/efts-io/compare/0.6.2...0.6.3)</small>

### Bug Fixes

- int64 station_id were read by xarray as floats before conversion to string in memory, leading to station ids such as "1234.0" ([6137ae5](https://github.com/csiro-hydroinformatics/efts-io/commit/6137ae55238480de1a0543d51f8887a84e0331d6) by J-M).

## [0.6.2](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.6.2) - 2025-11-27

<small>[Compare with 0.6.1](https://github.com/csiro-hydroinformatics/efts-io/compare/0.6.1...0.6.2)</small>

### Bug Fixes

- minor, make the API behavior consistent now that stations as strings are supported for input to STF2.0 writing ([d24a42f](https://github.com/csiro-hydroinformatics/efts-io/commit/d24a42fac3e647ab2ad97f3c12b5b839522fba04) by J-M).

## [0.6.1](https://github.com/csiro-hydroinformatics/efts-io/releases/tag/0.6.1) - 2025-11-18

<small>[Compare with 0.6.0](https://github.com/csiro-hydroinformatics/efts-io/compare/0.6.0...0.6.1)</small>

### Bug Fixes

- cannot write an a priori suitable xarray to stf2 ([8f8720f](https://github.com/csiro-hydroinformatics/efts-io/commit/8f8720f9381ddf51e677bf18c6f6279358ccecc9) by J-M).

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
