"""Low level functions to write an xarray DataArray to disk in the STF conventions.

These are functions ported from a collection of utilities initially in
https://bitbucket.csiro.au/projects/SF/repos/python_functions/browse/swift_utility/swift_io.py
"""

import os  # noqa: I001
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Any, Optional

from typing_extensions import Self

import numpy as np
import pandas as pd
import xarray as xr

from efts_io.conventions import (
    AREA_VARNAME,
    AXIS_ATTR_KEY,
    CATCHMENT_ATTR_KEY,
    COMMENT_ATTR_KEY,
    DAT_TYPE_ATTR_KEY,
    DAT_TYPE_DESCRIPTION_ATTR_KEY,
    ELEVATION_VARNAME,
    ENS_MEMBER_DIMNAME,
    FILLVALUE_ATTR_KEY,
    HISTORY_ATTR_KEY,
    INSTITUTION_ATTR_KEY,
    LAT_VARNAME,
    LEAD_TIME_DIMNAME,
    LOCATION_TYPE_ATTR_KEY,
    LON_VARNAME,
    LONG_NAME_ATTR_KEY,
    REALISATION_DIMNAME,
    SOURCE_ATTR_KEY,
    STANDARD_NAME_ATTR_KEY,
    STATION_DIMNAME,
    STATION_ID_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    STF_2_0_URL,
    STF_CONVENTION_VERSION_ATTR_KEY,
    STR_LEN_DIMNAME,
    TIME_DIMNAME,
    TIME_STANDARD_ATTR_KEY,
    TITLE_ATTR_KEY,
    TYPE_ATTR_KEY,
    TYPE_DESCRIPTION_ATTR_KEY,
    TYPES_CONVERTIBLE_TO_TIMESTAMP,
    UNITS_ATTR_KEY,
    X_VARNAME,
    Y_VARNAME,
    AttributesErrorLevel,
    DataOriginType,
    check_optional_variable_attributes,
    detect_timezone_info,
    has_required_variables_xr,
    has_required_xarray_global_attributes,
    has_variable,
    is_subset_required_xarray_dimensions,
    mandatory_global_attributes,
    mandatory_varnames_xr,
    mandatory_xarray_dimensions,
    validate_fixed_offset_timezone,
)

from netCDF4 import Dataset


# ---------------------------------------------------------------------------
# Public enums
# ---------------------------------------------------------------------------


class StfVariable(Enum):
    """Hydrological variable type in the STF convention."""

    STREAMFLOW = 1
    POTENTIAL_EVAPOTRANSPIRATION = 2
    RAINFALL = 3
    SNOW_WATER_EQUIVALENT = 4
    MINIMUM_TEMPERATURE = 5
    MAXIMUM_TEMPERATURE = 6


class StfDataType(Enum):
    """Deprecated. Use :class:`efts_io.DataOriginType` instead.

    .. deprecated::
        Use :class:`~efts_io.DataOriginType` for new code. Passing a
        ``StfDataType`` value to :func:`write_nc_stf2` or
        :meth:`~efts_io.EftsDataSet.save_to_stf2` will emit a
        :class:`DeprecationWarning` and will be removed in a future version.
    """

    DERIVED = 1
    FORECAST = 2
    OBSERVED = 3
    SIMULATED = 4


# Internal mapping from DataOriginType to the integer ordinal used by write_nc_stf2.
# The integers correspond to StfDataType values for backward compatibility.
_DATA_ORIGIN_TYPE_TO_INT: dict[DataOriginType, int] = {
    DataOriginType.DERIVED: StfDataType.DERIVED.value,
    DataOriginType.FORECAST: StfDataType.FORECAST.value,
    DataOriginType.OBSERVED: StfDataType.OBSERVED.value,
    DataOriginType.SIMULATED: StfDataType.SIMULATED.value,
}


# ---------------------------------------------------------------------------
# Variable naming metadata
# ---------------------------------------------------------------------------

# Mapping from StfVariable to its short prefix, long name, and default TimeSeriesType code.
_VARIABLE_META: dict[StfVariable, tuple[str, str, int]] = {
    StfVariable.STREAMFLOW: ("q", "streamflow", 3),
    StfVariable.POTENTIAL_EVAPOTRANSPIRATION: ("pet", "potential evapotranspiration", 2),
    StfVariable.RAINFALL: ("rain", "rainfall", 2),
    StfVariable.SNOW_WATER_EQUIVALENT: ("swe", "snow water equivalent", 2),
    StfVariable.MINIMUM_TEMPERATURE: ("tmin", "minimum temperature", 5),
    StfVariable.MAXIMUM_TEMPERATURE: ("tmax", "maximum temperature", 5),
}

# Mapping from TimeSeriesType code to its description.
_TIME_SERIES_TYPE_DESCRIPTIONS: dict[int, str] = {
    2: "accumulated over the preceding interval",
    3: "averaged over the preceding interval",
    5: "point value recorded in the preceding interval",
}

# STF version 1 uses "fcast" for forecast; version 2 uses "fct".
_FORECAST_SHORT: dict[int, str] = {1: "fcast", 2: "fct"}

# Mapping from DataOriginType to (short_name, long_name) for STF version 2.
# "derived" and "observed" map to "obs" category; "simulated" and "forecast" map to "sim".
_DATA_ORIGIN_OBS_SET: frozenset[DataOriginType] = frozenset({DataOriginType.DERIVED, DataOriginType.OBSERVED})


@dataclass(frozen=True)
class VariableNaming:
    """Resolved variable naming for a given var_type + data_type + version combination.

    Attributes:
        short_name: Short variable name written to the NetCDF file (e.g. ``"q_obs"``).
        long_name: Long descriptive name for the variable.
        default_ts_type_code: Default ``type`` attribute (TimeSeriesType integer code).
        default_ts_type_description: Default ``type_description`` attribute.
        dat_type: The ``dat_type`` attribute value (STF v2 only, e.g. ``"obs"``).
        dat_type_description: The ``dat_type_description`` attribute value (STF v2 only).
    """

    short_name: str
    long_name: str
    default_ts_type_code: int
    default_ts_type_description: str
    dat_type: str
    dat_type_description: str

    @classmethod
    def from_spec(
        cls,
        var_type: StfVariable,
        data_type: DataOriginType,
        stf_nc_vers: int,
        ens: bool,  # noqa: FBT001
    ) -> "VariableNaming":
        """Derive the naming from the STF convention specification.

        Args:
            var_type: Hydrological variable type.
            data_type: Data origin type.
            stf_nc_vers: STF convention version (1 or 2).
            ens: Whether this is an ensemble variable (version 1 only).

        Returns:
            A fully-resolved ``VariableNaming`` instance.
        """
        prefix, long_stem, ts_type_code = _VARIABLE_META[var_type]
        ts_type_desc = _TIME_SERIES_TYPE_DESCRIPTIONS[ts_type_code]

        dat_type_attr = ""
        dat_type_desc = ""

        if stf_nc_vers == 1:
            d_short = _stf1_data_type_short(data_type)
            d_long = _stf1_data_type_long(data_type)
            short_name = f"{prefix}_{d_short}"
            long_name = f"{d_long} {long_stem}"
            if ens:
                short_name = f"{short_name}_ens"
                long_name = f"{long_name} ensemble"
        else:
            dat_type_attr = data_type.code
            dat_type_desc = data_type.description
            if data_type in _DATA_ORIGIN_OBS_SET:
                short_name = f"{prefix}_obs"
                long_name = f"observed {long_stem}"
            else:
                short_name = f"{prefix}_sim"
                long_name = f"simulated {long_stem}"

        return cls(
            short_name=short_name,
            long_name=long_name,
            default_ts_type_code=ts_type_code,
            default_ts_type_description=ts_type_desc,
            dat_type=dat_type_attr,
            dat_type_description=dat_type_desc,
        )


def _stf1_data_type_short(data_type: DataOriginType) -> str:
    """Return the short data-type string for STF version 1."""
    mapping = {
        DataOriginType.DERIVED: "der",
        DataOriginType.FORECAST: "fcast",
        DataOriginType.OBSERVED: "obs",
        DataOriginType.SIMULATED: "sim",
    }
    return mapping[data_type]


def _stf1_data_type_long(data_type: DataOriginType) -> str:
    """Return the long data-type description for STF version 1."""
    mapping = {
        DataOriginType.DERIVED: "derived (from observations)",
        DataOriginType.FORECAST: "forecast",
        DataOriginType.OBSERVED: "observed",
        DataOriginType.SIMULATED: "simulated",
    }
    return mapping[data_type]


# ---------------------------------------------------------------------------
# Timestep normalisation
# ---------------------------------------------------------------------------

_TIMESTEP_ALIASES: dict[str, str] = {
    "weeks": "weeks", "w": "weeks", "wk": "weeks", "week": "weeks",
    "days": "days", "d": "days", "ds": "days", "day": "days",
    "hours": "hours", "h": "hours", "hr": "hours", "hour": "hours",
    "minutes": "minutes", "m": "minutes", "min": "minutes", "minute": "minutes",
    "seconds": "seconds", "s": "seconds", "sec": "seconds", "second": "seconds",
}


def _normalise_timestep(timestep: str) -> str:
    """Normalise a user-supplied timestep string to a canonical CF-compliant form.

    Args:
        timestep: A timestep alias (e.g. ``"d"``, ``"hr"``, ``"days"``).

    Returns:
        Canonical timestep string (one of ``"weeks"``, ``"days"``, ``"hours"``,
        ``"minutes"``, ``"seconds"``).

    Raises:
        ValueError: If the timestep is not recognised.
    """
    canonical = _TIMESTEP_ALIASES.get(timestep)
    if canonical is None:
        raise ValueError(f"Unsupported or unrecognised time step unit: {timestep}")
    return canonical


# ---------------------------------------------------------------------------
# CF time axis
# ---------------------------------------------------------------------------


def _create_cf_time_axis(data: xr.DataArray, timestep_str: str) -> tuple[np.ndarray, str, str, str]:
    """Create a CF-compliant time axis for the given xarray DataArray.

    This function detects the timezone from the input data and preserves it in the
    time axis encoding. Only fixed-offset timezones (no daylight saving time) are
    supported by the STF2 NetCDF format.

    Args:
        data: The input data array with time coordinate.
        timestep_str: The time step string (e.g., ``"days"``, ``"hours"``).

    Returns:
        A tuple containing:
            - encoded time axis values
            - units string with timezone
            - calendar string
            - timezone offset string (e.g., ``"+10:00"``, ``"-05:00"``, ``"+00:00"``)

    Raises:
        ValueError: If time array is empty.
        TypeError: If time values are not convertible to timestamps.
        NotImplementedError: If timezone observes daylight saving time (DST).
    """
    from xarray.coding import times

    tt = data[TIME_DIMNAME].values
    if len(tt) == 0:
        raise ValueError("Cannot create CF time axis from empty data array.")
    origin = tt[0]
    if not any(isinstance(origin, t) for t in TYPES_CONVERTIBLE_TO_TIMESTAMP):
        raise TypeError(
            f"Expected data[TIME_DIMNAME] to be of a type convertible to pd.Timestamp, got {type(origin)} instead.",
        )

    # Detect timezone from original timestamps
    tz_string, offset_string = detect_timezone_info(tt)

    # Validate that timezone is fixed-offset (no DST)
    origin_ts = pd.Timestamp(origin)
    tz_string, offset_string = validate_fixed_offset_timezone(tz_string, origin_ts)

    # If timezone-naive, treat as UTC
    if origin_ts.tz is None:
        origin_ts = origin_ts.tz_localize("UTC")

    # Format origin with timezone offset (ISO 8601 with space separator)
    formatted_string = origin_ts.strftime("%Y-%m-%d %H:%M:%S")
    formatted_string_with_tz = f"{formatted_string}{offset_string}"

    # xarray's encode_cf_datetime expects timezone-naive datetime values.
    # Convert timestamps to UTC and strip timezone info for encoding.
    # The timezone is preserved in the units string.
    dtimes_utc_naive = np.array(
        [
            pd.Timestamp(x).tz_convert("UTC").tz_localize(None) if pd.Timestamp(x).tz is not None else pd.Timestamp(x)
            for x in tt
        ],
        dtype="datetime64[ns]",
    )

    axis, _units, calendar = times.encode_cf_datetime(
        dates=dtimes_utc_naive,
        units=f"{timestep_str} since {formatted_string_with_tz}",
        calendar=None,
        dtype=None,
    )
    # Override units — encode_cf_datetime may vary the format.
    units = f"{timestep_str} since {formatted_string_with_tz}"
    return axis, units, calendar, offset_string


# ---------------------------------------------------------------------------
# Station ID validation
# ---------------------------------------------------------------------------


def _validate_station_id_for_int32(station_id: np.ndarray, intdata_type: str) -> None:
    """Validate that station_id values can be safely stored as int32.

    Args:
        station_id: Array of station ID values to validate.
        intdata_type: The intended integer data type (e.g., ``"i4"`` for int32).

    Raises:
        TypeError: If station_id values are not integers.
        OverflowError: If station_id values are outside the int32 range.
    """
    if intdata_type == "i4":
        max_station_id = np.max(station_id)
        min_station_id = np.min(station_id)
        if not np.issubdtype(type(max_station_id), np.integer) or not np.issubdtype(type(min_station_id), np.integer):
            raise TypeError("station_id values must be integers to be stored in STF2.0 format.")
        if max_station_id > np.iinfo(np.int32).max or min_station_id < np.iinfo(np.int32).min:
            raise OverflowError(
                f"station_id values must be in the int32 range [{np.iinfo(np.int32).min}, {np.iinfo(np.int32).max}] to be stored in STF2.0 format.",
            )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def _validate_inputs(
    dataset: xr.Dataset,
    data: xr.DataArray,
) -> None:
    """Validate that the dataset and data array meet STF requirements.

    Args:
        dataset: The xarray Dataset with global attributes and variables.
        data: The xarray DataArray to be written.

    Raises:
        ValueError: If required dimensions, attributes, or variables are missing.
    """
    if not is_subset_required_xarray_dimensions(data):
        raise ValueError(
            f"DataArray must have dimensions that are a subset of: {mandatory_xarray_dimensions}",
        )

    if not has_required_xarray_global_attributes(dataset):
        raise ValueError(
            f"DataArray must have the following global attributes: {mandatory_global_attributes}",
        )

    if not has_required_variables_xr(dataset):
        raise ValueError(
            f"DataArray must have the following variables: {mandatory_varnames_xr}",
        )

    for var_id in (AREA_VARNAME, X_VARNAME, Y_VARNAME, ELEVATION_VARNAME):
        if has_variable(dataset, var_id):
            check_optional_variable_attributes(dataset[var_id], AttributesErrorLevel.ERROR)


def _coerce_station_ids(dataset: xr.Dataset) -> np.ndarray:
    """Extract station IDs from the dataset, coercing to integer if necessary.

    Args:
        dataset: The xarray Dataset containing station_id values.

    Returns:
        Integer numpy array of station IDs.

    Raises:
        TypeError: If station_id values cannot be converted to integers.
    """
    station_id = dataset[STATION_ID_VARNAME].values
    if not np.issubdtype(station_id.dtype, np.integer):
        try:
            station_id = station_id.astype(np.int64)
        except Exception as e:
            raise TypeError(
                "station_id values must be representable as integers to be stored in STF2.0 format, "
                "and we could not convert them all automatically.",
            ) from e
    return station_id


def _handle_existing_file(out_nc_file: str, overwrite: bool) -> None:  # noqa: FBT001
    """Remove existing output file if overwrite is allowed, or raise.

    Args:
        out_nc_file: Path to the output NetCDF file.
        overwrite: Whether to overwrite an existing file.

    Raises:
        FileExistsError: If the file exists and ``overwrite`` is ``False``.
    """
    if os.path.exists(out_nc_file):
        if not overwrite:
            raise FileExistsError(
                f"Warning: The file '{out_nc_file}' exists, so either set overwrite=True to overwrite or give new filename.",
            )
        os.remove(out_nc_file)


# ---------------------------------------------------------------------------
# NetCDF file builder
# ---------------------------------------------------------------------------


class _StfFileBuilder:
    """Context manager that writes an STF NetCDF file.

    Usage::

        with _StfFileBuilder(path, ...) as builder:
            builder.write()
    """

    def __init__(
        self,
        path: str,
        dataset: xr.Dataset,
        data: xr.DataArray,
        naming: VariableNaming,
        data_type: DataOriginType,
        stf_nc_vers: int,
        timestep_str: str,
        intdata_type: str,
        data_qual: Optional[xr.DataArray],
    ) -> None:
        self._path = path
        self._dataset = dataset
        self._data = data
        self._naming = naming
        self._data_type = data_type
        self._stf_nc_vers = stf_nc_vers
        self._timestep_str = timestep_str
        self._intdata_type = intdata_type
        self._data_qual = data_qual
        self._ncfile: Optional[Dataset] = None

    # -- context manager ------------------------------------------------------

    def __enter__(self) -> Self:
        self._ncfile = Dataset(self._path, "w", format="NETCDF4")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._ncfile is None:
            return
        self._ncfile.close()
        if exc_type is not None and os.path.exists(self._path):
            os.remove(self._path)

    # -- public entry point ---------------------------------------------------

    def write(self) -> None:
        """Write the complete STF NetCDF file."""
        self._write_global_attributes()
        self._write_station_dimension()
        self._write_station_id()
        self._write_station_name()
        self._write_geolocation()
        self._write_optional_variables()
        self._prepare_data()
        self._write_lead_time_dimension()
        self._write_ensemble_dimension()
        self._write_time_dimension()
        self._write_data_variable()
        if self._data_qual is not None:
            self._write_quality_variable()

    # -- helpers --------------------------------------------------------------

    def _add_variable(
        self,
        name: str,
        dtype: str,
        dims: tuple[str, ...],
        data: np.ndarray,
        fill_value: Any = -9999,
        attrs: Optional[dict[str, Any]] = None,
    ) -> None:
        """Create a variable, set attributes, and assign data."""
        assert self._ncfile is not None  # noqa: S101
        var = self._ncfile.createVariable(name, dtype, dims, fill_value=fill_value)
        if attrs:
            for key, value in attrs.items():
                var.setncattr(key, value)
        var[:] = data

    # -- section writers ------------------------------------------------------

    def _write_global_attributes(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        ds_attrs = self._dataset.attrs
        nc.title = ds_attrs.get(TITLE_ATTR_KEY, "")
        nc.institution = ds_attrs.get(INSTITUTION_ATTR_KEY, "")
        nc.source = ds_attrs.get(SOURCE_ATTR_KEY, "")
        nc.catchment = ds_attrs.get(CATCHMENT_ATTR_KEY, "")
        nc.STF_convention_version = ds_attrs.get(STF_CONVENTION_VERSION_ATTR_KEY, "")
        nc.STF_nc_spec = STF_2_0_URL
        nc.comment = ds_attrs.get(COMMENT_ATTR_KEY, "")
        nc.history = ds_attrs.get(HISTORY_ATTR_KEY, "")

    def _write_station_dimension(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        n_stations = len(self._data[STATION_ID_DIMNAME])
        nc.createDimension(STATION_DIMNAME, n_stations)
        self._add_variable(
            STATION_DIMNAME,
            self._intdata_type,
            (STATION_DIMNAME,),
            np.arange(1, n_stations + 1),
        )

    def _write_station_id(self) -> None:
        station_id = _coerce_station_ids(self._dataset)
        _validate_station_id_for_int32(station_id, self._intdata_type)
        self._add_variable(
            STATION_ID_VARNAME,
            self._intdata_type,
            (STATION_DIMNAME,),
            station_id,
            attrs={LONG_NAME_ATTR_KEY: "station or node identification code"},
        )

    def _write_station_name(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        station_names = self._dataset[STATION_NAME_VARNAME].values
        str_len = 30
        nc.createDimension(STR_LEN_DIMNAME, str_len)
        station_name_var = nc.createVariable(STATION_NAME_VARNAME, "c", (STATION_DIMNAME, STR_LEN_DIMNAME))
        station_name_var.setncattr(LONG_NAME_ATTR_KEY, "station or node name")
        for idx, name in enumerate(station_names):
            padded = [" "] * str_len
            truncated = name[:str_len]
            padded[: len(truncated)] = truncated
            station_name_var[idx, :] = padded

    def _write_geolocation(self) -> None:
        self._add_variable(
            LAT_VARNAME, "f", (STATION_DIMNAME,),
            self._dataset[LAT_VARNAME].values,
            attrs={LONG_NAME_ATTR_KEY: "latitude", UNITS_ATTR_KEY: "degrees_north", AXIS_ATTR_KEY: "y"},
        )
        self._add_variable(
            LON_VARNAME, "f", (STATION_DIMNAME,),
            self._dataset[LON_VARNAME].values,
            attrs={LONG_NAME_ATTR_KEY: "longitude", UNITS_ATTR_KEY: "degrees_east", AXIS_ATTR_KEY: "x"},
        )

    def _write_optional_variables(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        for var_id in (AREA_VARNAME, X_VARNAME, Y_VARNAME, ELEVATION_VARNAME):
            if not has_variable(self._dataset, var_id):
                continue
            xrvar = self._dataset[var_id]
            var = nc.createVariable(var_id, "f", (STATION_DIMNAME,), fill_value=-9999)
            var[:] = xrvar.values
            for attr_key in (STANDARD_NAME_ATTR_KEY, LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY):
                var.setncattr(attr_key, xrvar.attrs[attr_key])

    def _prepare_data(self) -> None:
        """Expand and reorder data dimensions for the target NetCDF layout."""
        dimensions_order = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
        self._dimensions_order = dimensions_order
        self._data = make_ready_for_saving(self._data, self._dataset, dimensions_order)

    def _write_lead_time_dimension(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        lt_values = self._data[LEAD_TIME_DIMNAME].values
        nc.createDimension(LEAD_TIME_DIMNAME, len(lt_values))
        self._add_variable(
            LEAD_TIME_DIMNAME,
            self._intdata_type,
            (LEAD_TIME_DIMNAME,),
            lt_values,
            attrs={
                STANDARD_NAME_ATTR_KEY: "lead time",
                LONG_NAME_ATTR_KEY: "forecast lead time",
                UNITS_ATTR_KEY: "days since time",
                AXIS_ATTR_KEY: "v",
            },
        )

    def _write_ensemble_dimension(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        n_ens = len(self._data[REALISATION_DIMNAME])
        nc.createDimension(ENS_MEMBER_DIMNAME, n_ens)
        self._add_variable(
            ENS_MEMBER_DIMNAME,
            self._intdata_type,
            (ENS_MEMBER_DIMNAME,),
            np.arange(1, n_ens + 1),
            attrs={
                STANDARD_NAME_ATTR_KEY: ENS_MEMBER_DIMNAME,
                LONG_NAME_ATTR_KEY: "ensemble member",
                UNITS_ATTR_KEY: "member id",
                AXIS_ATTR_KEY: "u",
            },
        )

    def _write_time_dimension(self) -> None:
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        n_time = len(self._data[TIME_DIMNAME])
        nc.createDimension(TIME_DIMNAME, n_time)

        axis_values, time_units_str, _, timezone_offset = _create_cf_time_axis(self._data, self._timestep_str)
        self._add_variable(
            TIME_DIMNAME,
            self._intdata_type,
            (TIME_DIMNAME,),
            axis_values,
            attrs={
                STANDARD_NAME_ATTR_KEY: TIME_DIMNAME,
                LONG_NAME_ATTR_KEY: TIME_DIMNAME,
                TIME_STANDARD_ATTR_KEY: f"UTC{timezone_offset}",
                AXIS_ATTR_KEY: "t",
                UNITS_ATTR_KEY: time_units_str,
            },
        )

    def _write_data_variable(self) -> None:
        """Write the main hydrological data variable with its attributes."""
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        naming = self._naming
        data_attrs = self._data.attrs

        if UNITS_ATTR_KEY not in data_attrs:
            raise ValueError(
                f"DataArray variable '{self._data.name}' must have '{UNITS_ATTR_KEY}' attribute defined.",
            )

        attr_fillvalue = data_attrs.get(FILLVALUE_ATTR_KEY, -9999.0)

        var = nc.createVariable(
            naming.short_name,
            "f",
            self._dimensions_order,
            fill_value=attr_fillvalue,
        )

        var.setncattr(STANDARD_NAME_ATTR_KEY, naming.short_name)
        var.setncattr(LONG_NAME_ATTR_KEY, data_attrs.get(LONG_NAME_ATTR_KEY, naming.long_name))
        var.setncattr(UNITS_ATTR_KEY, data_attrs[UNITS_ATTR_KEY])

        var.setncattr(
            TYPE_ATTR_KEY,
            int(data_attrs.get(TYPE_ATTR_KEY, naming.default_ts_type_code)),
        )
        var.setncattr(
            TYPE_DESCRIPTION_ATTR_KEY,
            data_attrs.get(TYPE_DESCRIPTION_ATTR_KEY, naming.default_ts_type_description),
        )
        var.setncattr(LOCATION_TYPE_ATTR_KEY, data_attrs.get(LOCATION_TYPE_ATTR_KEY, "Point"))

        if int(self._stf_nc_vers) == 2:  # noqa: PLR2004
            var.setncattr(DAT_TYPE_ATTR_KEY, data_attrs.get(DAT_TYPE_ATTR_KEY, naming.dat_type))
            var.setncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY, naming.dat_type_description)

        var[:, :, :, :] = self._data.values[:]

    def _write_quality_variable(self) -> None:
        """Write the data quality variable."""
        nc = self._ncfile
        assert nc is not None  # noqa: S101
        assert self._data_qual is not None  # noqa: S101
        naming = self._naming

        qu_var_name_s = f"{naming.short_name}_qual"

        if int(self._stf_nc_vers) == 1:
            data_type_indx = _DATA_ORIGIN_TYPE_TO_INT[self._data_type] - 1
            if data_type_indx == 2:  # noqa: PLR2004  OBSERVED
                dims: tuple[str, ...] = (TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
            else:
                dims = (TIME_DIMNAME, STATION_DIMNAME)
        else:
            dims = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)

        var = nc.createVariable(qu_var_name_s, "f", dims, fill_value=-1)
        var[:] = self._data_qual.values[:]

        var.setncattr(STANDARD_NAME_ATTR_KEY, qu_var_name_s)
        var.setncattr(LONG_NAME_ATTR_KEY, f"{naming.long_name} data quality")
        var.setncattr(UNITS_ATTR_KEY, self._data_qual.attrs.get("quality_code", "Quality codes"))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def write_nc_stf2(
    out_nc_file: str,
    dataset: xr.Dataset,
    data: xr.DataArray,
    var_type: StfVariable = StfVariable.STREAMFLOW,
    data_type: DataOriginType = DataOriginType.OBSERVED,
    stf_nc_vers: int = 2,
    ens: bool = False,  # noqa: FBT001, FBT002
    timestep: str = "days",
    data_qual: Optional[xr.DataArray] = None,
    overwrite: bool = True,  # noqa: FBT001, FBT002
    intdata_type: str = "i4",
) -> None:
    """Write an xarray DataArray to a NetCDF file following the STF conventions.

    Args:
        out_nc_file: Path to the output NetCDF file.
        dataset: xarray Dataset containing coordinates, variables and global attributes.
        data: xarray DataArray with the hydrological data to write.
        var_type: Type of hydrological variable.
        data_type: Data origin type.
        stf_nc_vers: STF convention version (1 or 2).
        ens: Whether this is an ensemble variable (version 1 only).
        timestep: Time step unit string (e.g. ``"days"``, ``"hours"``, ``"h"``).
        data_qual: Optional quality-flag DataArray.
        overwrite: Whether to overwrite an existing file.
        intdata_type: NetCDF integer type for dimension variables (``"i4"`` or ``"i8"``).
    """
    _validate_inputs(dataset, data)
    naming = VariableNaming.from_spec(var_type, data_type, stf_nc_vers, ens)
    timestep_str = _normalise_timestep(timestep)
    _handle_existing_file(out_nc_file, overwrite)

    with _StfFileBuilder(
        path=out_nc_file,
        dataset=dataset,
        data=data,
        naming=naming,
        data_type=data_type,
        stf_nc_vers=stf_nc_vers,
        timestep_str=timestep_str,
        intdata_type=intdata_type,
        data_qual=data_qual,
    ) as builder:
        builder.write()


def make_ready_for_saving(data: xr.DataArray, dataset: xr.Dataset, dimensions_order: tuple) -> xr.DataArray:
    """Transform an xarray DataArray to ensure it has all required dimensions in the correct order for saving to NetCDF.

    Uses the coordinates from the parent dataset when expanding dimensions if required.

    Args:
        data: Input data array with xarray dimensions naming convention.
            Coordinates names must be one or several of TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME
        dataset: Parent xarray dataset containing coordinate information
            Coordinates names must include TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME
        dimensions_order: Expected order of target dimensions in the output NetCDF file, in fine.
            It must a tuple combining one of the values TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, ENS_MEMBER_DIMNAME

    Returns:
        Data array with all required dimensions in the correct order

    Raises:
        ValueError: Unexpected dimension in the dataarray, not in
    """
    from efts_io.conventions import xr_to_stf_dims, stf_to_xr_dims  # noqa: I001

    known_xr_dims = tuple(xr_to_stf_dims.keys())
    present_xr_dims = tuple(data.sizes.keys())
    if not set(present_xr_dims).intersection(known_xr_dims) == set(present_xr_dims):
        raise ValueError(
            f"DataArray dimensions {present_xr_dims} is not a subset of expected dimensions: {known_xr_dims}",
        )
    missing_xr_dims = list(set(known_xr_dims).difference(set(present_xr_dims)))

    # check that the missing_xr_dims in the `dataset` are all of length one:
    for xr_dim in missing_xr_dims:
        if xr_dim not in dataset.coords:
            raise ValueError(f"Dimension '{xr_dim}' is missing from the dataset coordinates.")
        if dataset.coords[xr_dim].size != 1:
            raise ValueError(
                f"Dimension '{xr_dim}' is missing from the data array and cannot be added because it has more than one value in the dataset.",
            )

    if len(missing_xr_dims) > 0:
        # expand result with the one-length dimensions present in the dataset but not coords of the dataarray:
        result = data.expand_dims({xr_dim: dataset.coords[xr_dim] for xr_dim in missing_xr_dims})
    else:
        result = data

    # Build a list of xarray dimension names in the order specified by dimensions_order
    ordered_xr_dims = []
    if result.dims == dimensions_order:
        return result.copy()
    for stf_dim in dimensions_order:
        xr_dim = stf_to_xr_dims.get(stf_dim, stf_dim)
        ordered_xr_dims.append(xr_dim)

    # Transpose to get the desired dimension order
    # copy as a fallback, in case we have a degenerate case.
    return result.transpose(*ordered_xr_dims) if ordered_xr_dims else result.copy()
