"""Naming conventions for the EFTS netCDF file format."""

from datetime import datetime  # noqa: I001
from typing import Any, Union
from collections.abc import Iterable

import numpy as np
import pandas as pd
import xarray as xr
from enum import Enum

# It may be important to import this AFTER xarray...
import netCDF4 as nc  # noqa: N813

ConvertibleToTimestamp = Union[str, datetime, np.datetime64, pd.Timestamp]
TYPES_CONVERTIBLE_TO_TIMESTAMP = [str, datetime, np.datetime64, pd.Timestamp]
"""Definition of a 'type' for type hints.
"""


TIME_DIMNAME = "time"
STATION_DIMNAME = "station"
ENS_MEMBER_DIMNAME = "ens_member"
LEAD_TIME_DIMNAME = "lead_time"
STR_LEN_DIMNAME = "strLen"

# New names for in-memory representation in an xarray way
# https://github.com/csiro-hydroinformatics/efts-io/issues/2
STATION_ID_DIMNAME = "station_id"

# a bit of research, albeit probably biased by nature (Gemini deep research),
# indicates a resignation to submit to US spelling on this front.
# Je passe a autre chose, mais je n'en pense pas moins.
REALISATION_DIMNAME = "realization"

# int station_id[station]
STATION_ID_VARNAME = "station_id"
# char station_name[str_len,station]
STATION_NAME_VARNAME = "station_name"
# float lat[station]
LAT_VARNAME = "lat"
# float lon[station]
LON_VARNAME = "lon"
# float x[station]
X_VARNAME = "x"
# float y[station]
Y_VARNAME = "y"
# float area[station]
AREA_VARNAME = "area"
# float elevation[station]
ELEVATION_VARNAME = "elevation"

conventional_varnames_mandatory = [
    STATION_DIMNAME,
    LEAD_TIME_DIMNAME,
    TIME_DIMNAME,
    ENS_MEMBER_DIMNAME,
    STR_LEN_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    LAT_VARNAME,
    LON_VARNAME,
]

conventional_varnames_optional = [
    X_VARNAME,
    Y_VARNAME,
    AREA_VARNAME,
    ELEVATION_VARNAME,
]

conventional_varnames = conventional_varnames_mandatory + conventional_varnames_optional

hydro_varnames = ("rain", "pet", "q", "swe", "tmin", "tmax", "tave")
var_type = ("obs", "sim")
obs_hydro_varnames = tuple(f"{var}_{var_type[0]}" for var in hydro_varnames)
sim_hydro_varnames = tuple(f"{var}_{var_type[1]}" for var in hydro_varnames)
obs_hydro_varnames_qual = tuple(f"{x}_qual" for x in obs_hydro_varnames)
sim_hydro_varnames_qual = tuple(f"{x}_qual" for x in sim_hydro_varnames)
known_hydro_varnames = obs_hydro_varnames + sim_hydro_varnames + obs_hydro_varnames_qual + sim_hydro_varnames_qual

# TODO: perhaps deal with the state variable names. But, is it used in practice?

TITLE_ATTR_KEY = "title"
INSTITUTION_ATTR_KEY = "institution"
SOURCE_ATTR_KEY = "source"
CATCHMENT_ATTR_KEY = "catchment"
STF_CONVENTION_VERSION_ATTR_KEY = "STF_convention_version"
STF_NC_SPEC_ATTR_KEY = "STF_nc_spec"
COMMENT_ATTR_KEY = "comment"
HISTORY_ATTR_KEY = "history"

TIME_STANDARD_ATTR_KEY = "time_standard"
STANDARD_NAME_ATTR_KEY = "standard_name"
LONG_NAME_ATTR_KEY = "long_name"
AXIS_ATTR_KEY = "axis"
UNITS_ATTR_KEY = "units"

FILLVALUE_ATTR_KEY = "_FillValue"
TYPE_ATTR_KEY = "type"
TYPE_DESCRIPTION_ATTR_KEY = "type_description"
DAT_TYPE_DESCRIPTION_ATTR_KEY = "dat_type_description"
DAT_TYPE_ATTR_KEY = "dat_type"
LOCATION_TYPE_ATTR_KEY = "location_type"

MODEL_NAME_ATTR_KEY = "model_name"
SV_NAME_ATTR_KEY = "sv_name"
SV_DESCRIPTION_ATTR_KEY = "sv_description"

# We use a URL at a specific commit point, to be used as a file attribute.
# STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts/blob/d7d43a995fb5e459bcb894e09b7bb89de03e285c/docs/netcdf_for_water_forecasting.md"
# July 2025, set a new location/commit point:
# STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts-io/blob/42ee35f0f019e9bad48b94914429476a7e8278dc/docs/netcdf_for_water_forecasting.md"
# March 2026, update to a new commit point, with fixes and changes ported from the latest version of the specs on CSIRO confluence:
STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts-io/blob/1ce25adbda8b49f383150f268e76c8c415746592/docs/netcdf_for_water_forecasting.md"


mandatory_global_attributes_xr = [
    TITLE_ATTR_KEY,
    INSTITUTION_ATTR_KEY,
    SOURCE_ATTR_KEY,
    CATCHMENT_ATTR_KEY,
    COMMENT_ATTR_KEY,
    HISTORY_ATTR_KEY,
]

mandatory_global_attributes = [
    TITLE_ATTR_KEY,
    INSTITUTION_ATTR_KEY,
    SOURCE_ATTR_KEY,
    CATCHMENT_ATTR_KEY,
    STF_CONVENTION_VERSION_ATTR_KEY,
    STF_NC_SPEC_ATTR_KEY,
    COMMENT_ATTR_KEY,
    HISTORY_ATTR_KEY,
]

mandatory_netcdf_dimensions = [TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, STR_LEN_DIMNAME, ENS_MEMBER_DIMNAME]
mandatory_xarray_dimensions = [TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME]

# mappings to help automatic handling between stf and in memory dimensions
stf_to_xr_dims = {
    TIME_DIMNAME: TIME_DIMNAME,
    ENS_MEMBER_DIMNAME: REALISATION_DIMNAME,
    STATION_DIMNAME: STATION_ID_DIMNAME,
    LEAD_TIME_DIMNAME: LEAD_TIME_DIMNAME,
}

xr_to_stf_dims = {
    TIME_DIMNAME: TIME_DIMNAME,
    REALISATION_DIMNAME: ENS_MEMBER_DIMNAME,
    STATION_ID_DIMNAME: STATION_DIMNAME,
    LEAD_TIME_DIMNAME: LEAD_TIME_DIMNAME,
}

mandatory_varnames_xr = [
    TIME_DIMNAME,
    LEAD_TIME_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    REALISATION_DIMNAME,
    LAT_VARNAME,
    LON_VARNAME,
]


class AttributesErrorLevel(Enum):
    """Controls the behavior of variable attribute checking functions."""

    NONE = 1
    ERROR = 2
    # WARNING = 3


def get_default_dim_order() -> list[str]:
    """Default order of dimensions in the netCDF file.

    Returns:
        List[str]: dimension names: [lead_time, stations, ensemble_member, time]
    """
    return [
        LEAD_TIME_DIMNAME,
        STATION_DIMNAME,
        ENS_MEMBER_DIMNAME,
        TIME_DIMNAME,
    ]


def check_index_found(
    index_id: int | None,
    identifier: str,
    dimension_id: str,
) -> None:
    """Helper function to check that a value (index) was is indeed found in the dimension."""
    # return isinstance(index_id, np.int64)
    if index_id is None:
        raise ValueError(
            f"identifier '{identifier}' not found in the dimension '{dimension_id}'",
        )


# MdDatasetsType = Union[nc.Dataset, xr.Dataset, xr.DataArray]
MdDatasetsType = Union[xr.Dataset, xr.DataArray]


def _is_nc_dataset(d: Any) -> bool:
    return isinstance(d, nc.Dataset)


def _is_nc_variable(d: Any) -> bool:
    return isinstance(d, nc.Variable)


def _is_ncdf4_withattrs(d: Any) -> bool:
    return _is_nc_dataset(d) or _is_nc_variable(d)


def _has_required_dimensions(
    d: MdDatasetsType,
    mandatory_dimensions: Iterable[str],
) -> bool:
    if _is_nc_dataset(d):
        return set(d.dimensions.keys()) == set(mandatory_dimensions)
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        # FutureWarning: The return type of `Dataset.dims` will be changed
        # to return a set of dimension names in future, in order to be more
        # consistent with `DataArray.dims`.
        dims = d.dims
        # work around legacy discrepancy between data arrays and datasets: list and dict.
        kk = set([k for k in dims])  # noqa: C403, C416
        return kk == set(mandatory_dimensions)


def _is_subset_required_dimensions(
    d: MdDatasetsType,
    mandatory_dimensions: Iterable[str],
) -> bool:
    if _is_nc_dataset(d):
        d_set = set(d.dimensions.keys())
        return d_set.intersection(set(mandatory_dimensions)) == d_set
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        # FutureWarning: The return type of `Dataset.dims` will be changed
        # to return a set of dimension names in future, in order to be more
        # consistent with `DataArray.dims`.
        dims = d.dims
        # work around legacy discrepancy between data arrays and datasets: list and dict.
        d_set = set([k for k in dims])  # noqa: C403, C416
        return d_set.intersection(set(mandatory_dimensions)) == d_set


def has_required_stf2_dimensions(d: MdDatasetsType, mandatory_dimensions: Iterable[str] | None = None) -> bool:
    """Has the dataset the required dimensions for STF conventions.

    Args:
        d (MdDatasetsType): data object to check

    Returns:
        bool: Has it the minimum STF dimentions
    """
    mandatory_dimensions = mandatory_dimensions or mandatory_netcdf_dimensions
    return _has_required_dimensions(d, mandatory_dimensions)


def has_required_xarray_dimensions(d: MdDatasetsType) -> bool:
    """Has the dataset the required dimensions for an in memory xarray representation."""
    return _has_required_dimensions(d, mandatory_xarray_dimensions)


def is_subset_required_xarray_dimensions(d: MdDatasetsType) -> bool:
    """Has the data array or dataset dimensions that are a subset of the spedified dims?"""
    return _is_subset_required_dimensions(d, mandatory_xarray_dimensions)


def _has_all_members(tested: Iterable[str], reference: Iterable[str]) -> bool:
    """Tests whether all the expected members are present in the tested set."""
    r = set(reference)
    return set(tested).intersection(r) == r


def has_required_global_attributes(d: MdDatasetsType) -> bool:
    """has_required_global_attributes."""
    if _is_nc_dataset(d):
        a = d.ncattrs()
        tested = set(a)
    else:
        a = d.attrs.keys()
        tested = set(a)
    return _has_all_members(tested, mandatory_global_attributes)


def has_required_xarray_global_attributes(d: MdDatasetsType) -> bool:
    """has_required_xarray_global_attributes."""
    a = d.attrs.keys()
    tested = set(a)
    return _has_all_members(tested, mandatory_global_attributes_xr)


def has_required_variables_xr(d: MdDatasetsType) -> bool:
    """has_required_variables."""
    a = d.variables.keys()
    tested = set(a)
    # Note: even if xarray, we do not need to check for the 'data_vars' attribute here.
    # a = d.data_vars.keys()
    # tested = set(a)
    return _has_all_members(tested, mandatory_varnames_xr)


def has_variable(d: MdDatasetsType, varname: str) -> bool:
    """has_variable."""
    a = d.variables.keys()
    tested = set(a)
    return varname in tested


def check_stf_compliance(file_path: str) -> dict[str, list[str]]:
    """Checks the compliance of a netCDF file with the STF convention.

    Args:
        file_path (str): The path to the netCDF file.

    Returns:
        Dict[str, List[str]]: A dictionary with keys "INFO", "WARNING", "ERROR" and values as lists of strings describing compliance issues.
    """
    try:
        dataset = nc.Dataset(file_path, mode="r")
        results = {"INFO": [], "WARNING": [], "ERROR": []}

        # Check for required dimensions
        required_dims = [TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, ENS_MEMBER_DIMNAME, STR_LEN_DIMNAME]
        available_dims = dataset.dimensions.keys()

        for dim in required_dims:
            if dim in available_dims:
                results["INFO"].append(f"Dimension '{dim}' is present.")
            else:
                results["ERROR"].append(f"Missing required dimension '{dim}'.")

        # Check global attributes
        required_global_attributes = [
            TITLE_ATTR_KEY,
            INSTITUTION_ATTR_KEY,
            SOURCE_ATTR_KEY,
            CATCHMENT_ATTR_KEY,
            STF_CONVENTION_VERSION_ATTR_KEY,
            STF_NC_SPEC_ATTR_KEY,
            COMMENT_ATTR_KEY,
            HISTORY_ATTR_KEY,
        ]
        available_global_attributes = dataset.ncattrs()

        for attr in required_global_attributes:
            if attr in available_global_attributes:
                results["INFO"].append(f"Global attribute '{attr}' is present.")
            else:
                results["WARNING"].append(f"Missing global attribute '{attr}'.")

        # Check mandatory variables and their attributes
        mandatory_variables = [
            TIME_DIMNAME,
            STATION_ID_VARNAME,
            STATION_NAME_VARNAME,
            ENS_MEMBER_DIMNAME,
            LEAD_TIME_DIMNAME,
            LAT_VARNAME,
            LON_VARNAME,
        ]
        variable_attributes = {
            TIME_DIMNAME: [
                STANDARD_NAME_ATTR_KEY,
                LONG_NAME_ATTR_KEY,
                UNITS_ATTR_KEY,
                TIME_STANDARD_ATTR_KEY,
                AXIS_ATTR_KEY,
            ],
            STATION_ID_VARNAME: [LONG_NAME_ATTR_KEY],
            STATION_NAME_VARNAME: [LONG_NAME_ATTR_KEY],
            ENS_MEMBER_DIMNAME: [STANDARD_NAME_ATTR_KEY, LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY, AXIS_ATTR_KEY],
            LEAD_TIME_DIMNAME: [STANDARD_NAME_ATTR_KEY, LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY, AXIS_ATTR_KEY],
            LAT_VARNAME: [LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY, AXIS_ATTR_KEY],
            LON_VARNAME: [LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY, AXIS_ATTR_KEY],
        }

        for var in mandatory_variables:
            if var in dataset.variables:
                results["INFO"].append(f"Mandatory variable '{var}' is present.")
                # Check attributes
                for attr, required_attrs in variable_attributes.items():
                    if var == attr:
                        for req_attr in required_attrs:
                            if req_attr in dataset.variables[var].ncattrs():
                                results["INFO"].append(f"Attribute '{req_attr}' for variable '{var}' is present.")
                            else:
                                results["WARNING"].append(
                                    f"Missing required attribute '{req_attr}' for variable '{var}'.",
                                )
            else:
                results["ERROR"].append(f"Missing mandatory variable '{var}'.")

        dataset.close()
        return results  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        return {"ERROR": [f"Error opening file '{file_path}': {e!s}"]}


def _is_structural_varname(name: str) -> bool:
    return name in conventional_varnames


def _is_known_hydro_varname(name: str) -> bool:
    """Checks if the variable name is a known hydrologic variable."""
    # TODO: perhaps deal with state variable conventional names.
    return name in known_hydro_varnames


def _is_observation_variable(name: str) -> bool:
    return name in obs_hydro_varnames


def _is_simulation_variable(name: str) -> bool:
    return name in sim_hydro_varnames


def _is_quality_variable(name: str) -> bool:
    return name in obs_hydro_varnames_qual or name in sim_hydro_varnames_qual


def _extract_var_type(variable: Any) -> str:
    if _is_observation_variable(variable):
        return "obs"
    if _is_simulation_variable(variable):
        return "sim"
    if _is_quality_variable(variable):
        return "qual"
    return None


def _check_variable_attributes_obs(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    """Checks if the attributes of the observed variable comply with the conventions."""
    missing_attributes_messages = []
    required_attributes = {
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: float,
        TYPE_ATTR_KEY: int,
        TYPE_DESCRIPTION_ATTR_KEY: str,
        DAT_TYPE_ATTR_KEY: str,
        LOCATION_TYPE_ATTR_KEY: str,
    }
    return _check_attrs(variable, required_attributes, missing_attributes_messages, error_threshold=error_threshold)


def _check_variable_attributes_sim(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    """Checks if the attributes of the simulated variable comply with the conventions."""
    missing_attributes_messages = []
    required_attributes = {
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: float,
        TYPE_ATTR_KEY: int,
        TYPE_DESCRIPTION_ATTR_KEY: str,
        DAT_TYPE_ATTR_KEY: str,
        LOCATION_TYPE_ATTR_KEY: str,
    }
    return _check_attrs(variable, required_attributes, missing_attributes_messages, error_threshold=error_threshold)


def _check_variable_attributes_qual(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    """Checks if the attributes of the data quality code variable comply with the conventions."""
    missing_attributes_messages = []
    required_attributes = {
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: int,
        LOCATION_TYPE_ATTR_KEY: str,
        TYPE_DESCRIPTION_ATTR_KEY: str,
        DAT_TYPE_ATTR_KEY: str,
    }
    return _check_attrs(variable, required_attributes, missing_attributes_messages, error_threshold=error_threshold)


def _check_attrs_ncdataset(
    variable: Any,
    required_attributes: dict[str, type],
    missing_attributes_messages: list[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    for attr, attr_type in required_attributes.items():
        if attr not in variable.ncattrs():
            missing_attributes_messages.append(f"Missing required attribute '{attr}' for variable '{variable.name}'.")
        else:
            actual_type = type(variable.getncattr(attr))
            if actual_type != attr_type:
                missing_attributes_messages.append(
                    f"Attribute '{attr}' for variable '{variable.name}' has an unexpected type '{actual_type.__name__}'. Expected type: '{attr_type.__name__}'.",
                )
    if error_threshold == AttributesErrorLevel.ERROR and missing_attributes_messages:
        raise ValueError(
            f"Variable '{variable.name}' has missing or incorrect attributes: {missing_attributes_messages}",
        )
    return missing_attributes_messages


def _check_attrs_xr(
    variable: MdDatasetsType,
    required_attributes: dict[str, type],
    missing_attributes_messages: list[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    for attr, attr_type in required_attributes.items():
        if attr not in variable.attrs:
            missing_attributes_messages.append(f"Missing required attribute '{attr}' for variable '{variable.name}'.")
        else:
            actual_type = type(variable.attrs[attr])
            if actual_type != attr_type:
                missing_attributes_messages.append(
                    f"Attribute '{attr}' for variable '{variable.name}' has an unexpected type '{actual_type.__name__}'. Expected type: '{attr_type.__name__}'.",
                )
    if error_threshold == AttributesErrorLevel.ERROR and missing_attributes_messages:
        raise ValueError(
            f"Variable '{variable.name}' has missing or incorrect attributes: {missing_attributes_messages}",
        )
    return missing_attributes_messages


def _check_attrs(
    variable: Any,
    required_attributes: dict[str, type],
    missing_attributes_messages: list[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    if _is_ncdf4_withattrs(variable):
        return _check_attrs_ncdataset(variable, required_attributes, missing_attributes_messages, error_threshold)
    else:  # noqa: RET505
        return _check_attrs_xr(variable, required_attributes, missing_attributes_messages, error_threshold)


def _check_variable_attributes(variable: Any) -> list[str]:
    """Checks if the attributes of a variable comply with the conventions depending on the type of variable.

    Args:
        variable (Any): The netCDF variable whose attributes are to be checked.

    Returns:
        List[str]: A list of messages describing any missing attributes.
    """
    var_type = _extract_var_type(variable.name)

    if var_type == "obs":
        return _check_variable_attributes_obs(variable)
    if var_type == "sim":
        return _check_variable_attributes_sim(variable)
    if var_type == "qual":
        return _check_variable_attributes_qual(variable)

    return []


def check_hydrologic_variables(file_path: str) -> dict[str, list[str]]:
    """Checks if the variable names and attributes in a netCDF file comply with the STF convention.

    Args:
        file_path (str): The path to the netCDF file.

    Returns:
        Dict[str, List[str]]: A dictionary with keys "INFO", "WARNING", "ERROR" and values as lists of strings describing compliance issues.
    """
    try:
        dataset = None
        dataset = nc.Dataset(file_path, mode="r")
        results = {"INFO": [], "WARNING": [], "ERROR": []}

        for var in dataset.variables:
            if _is_structural_varname(var):
                continue
            if _is_known_hydro_varname(var):
                results["INFO"].append(f"Hydrologic variable '{var}' follows the recommended naming convention.")

                # Check attributes
                for msg in _check_variable_attributes(dataset.variables[var]):
                    results["WARNING"].append(msg)
            else:
                results["WARNING"].append(
                    f"Hydrologic variable '{var}' does not follow the recommended naming convention.",
                )

        return results  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        return {"ERROR": [f"Error opening or reading file '{file_path}': {e!s}"]}

    finally:
        if dataset:
            dataset.close()


def check_optional_variable_attributes(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> list[str]:
    """Checks if the attributes of the observed variable comply with the conventions."""
    missing_attributes_messages = []
    required_attributes = {
        STANDARD_NAME_ATTR_KEY: str,
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
    }
    return _check_attrs(variable, required_attributes, missing_attributes_messages, error_threshold=error_threshold)


def convert_to_datetime64_utc(x: ConvertibleToTimestamp) -> np.datetime64:
    """Converts a known timestamp representation an np.datetime64."""
    if isinstance(x, pd.Timestamp):
        if x.tz is None:
            x = x.tz_localize("UTC")
        x = x.tz_convert("UTC")
    elif isinstance(x, datetime):
        x = pd.Timestamp(x, tz="UTC") if x.tzinfo is None else pd.Timestamp(x).tz_convert("UTC")
    elif isinstance(x, str):
        x_dt = pd.to_datetime(x)
        x = pd.Timestamp(x_dt, tz="UTC") if x_dt.tzinfo is None else pd.Timestamp(x_dt).tz_convert("UTC")
    elif isinstance(x, np.datetime64):
        x = pd.Timestamp(x).tz_localize("UTC")
    else:
        raise TypeError(f"Cannot convert {type(x)} to np.datetime64 with UTC timezone.")

    return x.to_datetime64()


def detect_timezone_info(
    timestamps: pd.DatetimeIndex | Iterable[ConvertibleToTimestamp] | ConvertibleToTimestamp,
) -> tuple[str, str]:
    """Detect timezone information from timestamps.

    This function extracts timezone information from various timestamp representations
    and returns both the timezone string and the formatted UTC offset.

    Args:
        timestamps: Timestamps as DatetimeIndex, iterable of timestamps, or single timestamp

    Returns:
        Tuple of (timezone_string, utc_offset_string) where:
        - timezone_string: Original timezone name (e.g., "UTC", "UTC+10:00", "America/New_York")
        - utc_offset_string: Formatted offset string (e.g., "+00:00", "+10:00", "-05:00")

    Note:
        Timezone-naive timestamps are treated as UTC and return ("UTC", "+00:00").
        UTC aliases (UTC, GMT, Etc/UTC) are normalized to ("UTC", "+00:00").

    Raises:
        ValueError: If timestamps is an empty collection
        TypeError: If timestamps type cannot be processed

    Examples:
        >>> import pandas as pd
        >>> timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+10:00")
        >>> detect_timezone_info(timestamps)
        ('UTC+10:00', '+10:00')

        >>> timestamps = pd.date_range("2024-01-01", periods=3)  # naive
        >>> detect_timezone_info(timestamps)
        ('UTC', '+00:00')
    """
    # Extract a sample timestamp to detect timezone
    sample_ts = None
    tz = None

    if isinstance(timestamps, pd.DatetimeIndex):
        if len(timestamps) == 0:
            raise ValueError("Cannot detect timezone from empty DatetimeIndex")
        sample_ts = timestamps[0]
        tz = timestamps.tz
    elif isinstance(timestamps, (list, tuple, np.ndarray)):
        if len(timestamps) == 0:
            raise ValueError("Cannot detect timezone from empty list/tuple")
        sample_item = timestamps[0]
        if isinstance(sample_item, pd.Timestamp):
            sample_ts = sample_item
            tz = sample_item.tz
        else:
            # Convert to Timestamp to check timezone
            sample_ts = pd.Timestamp(sample_item)
            tz = sample_ts.tz
    elif isinstance(timestamps, pd.Timestamp):
        sample_ts = timestamps
        tz = timestamps.tz
    elif isinstance(timestamps, (str, datetime, np.datetime64)):
        sample_ts = pd.Timestamp(timestamps)
        tz = sample_ts.tz
    elif isinstance(timestamps, xr.DataArray):
        # Handle xarray DataArray - extract the underlying index or values
        if len(timestamps) == 0:
            raise ValueError("Cannot detect timezone from empty DataArray")
        # Try to get pandas index which preserves timezone info
        try:
            idx = timestamps.to_index()
            if isinstance(idx, pd.DatetimeIndex):
                sample_ts = idx[0]
                tz = idx.tz
            else:
                # Fallback: convert first value to Timestamp
                sample_ts = pd.Timestamp(timestamps.values[0])
                tz = sample_ts.tz
        except (AttributeError, TypeError):
            # Fallback: convert first value to Timestamp
            sample_ts = pd.Timestamp(timestamps.values[0])
            tz = sample_ts.tz
    else:
        raise TypeError(f"Cannot detect timezone from type {type(timestamps)}")

    # Handle timezone-naive case
    if tz is None:
        return ("UTC", "+00:00")

    # Get timezone string
    tz_string = str(tz)

    # Normalize UTC aliases
    if tz_string in ["UTC", "GMT", "Etc/UTC"]:
        return ("UTC", "+00:00")

    # Get UTC offset from the sample timestamp
    # Ensure sample_ts is timezone-aware
    if sample_ts.tz is None:
        sample_ts = sample_ts.tz_localize(tz)

    # Get the offset
    offset = sample_ts.utcoffset()
    if offset is None:
        # This shouldn't happen if tz is not None, but handle it
        return (tz_string, "+00:00")

    # Convert to seconds and format as +HH:MM or -HH:MM
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    abs_seconds = abs(total_seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60
    offset_string = f"{sign}{hours:02d}:{minutes:02d}"

    return (tz_string, offset_string)


def validate_fixed_offset_timezone(
    timezone_string: str,
    sample_timestamp: pd.Timestamp | None = None,
) -> tuple[str, str]:
    """Validate that a timezone has a fixed UTC offset (no daylight saving time).

    This function checks if a timezone has daylight saving time (DST) transitions.
    NetCDF's CF time encoding format requires a fixed UTC offset in the format
    "time_units since ORIGIN +OFFSET", which cannot handle variable offsets.

    Args:
        timezone_string: Timezone name (e.g., "UTC", "UTC+10:00", "US/Eastern", "Australia/Sydney")
        sample_timestamp: Optional timestamp in the timezone for extracting offset.
                         If None, uses current time.

    Returns:
        Tuple of (normalized_timezone_string, utc_offset_string) for valid fixed-offset timezones

    Raises:
        NotImplementedError: If timezone observes daylight saving time (DST)
        ValueError: If timezone string is invalid or cannot be parsed

    Examples:
        >>> validate_fixed_offset_timezone("UTC")
        ('UTC', '+00:00')

        >>> validate_fixed_offset_timezone("UTC+10:00")
        ('UTC+10:00', '+10:00')

        >>> validate_fixed_offset_timezone("US/Eastern")  # doctest: +SKIP
        Traceback (most recent call last):
        ...
        NotImplementedError: Timezones with daylight saving time (DST) are not supported...
    """
    # Normalize UTC aliases first
    if timezone_string in ["UTC", "GMT", "Etc/UTC"]:
        return ("UTC", "+00:00")

    # Try to parse the timezone
    tz = None
    try:
        # Try to use zoneinfo (Python 3.9+) to check for DST transitions
        try:
            from zoneinfo import ZoneInfo

            tz = ZoneInfo(timezone_string)
        except (ImportError, ModuleNotFoundError, KeyError):
            # Fall back to using dateutil or pytz
            # KeyError is raised when ZoneInfo can't find the timezone (e.g., for fixed offset strings like "UTC-08:00")
            try:
                from dateutil import tz as dateutil_tz

                tz = dateutil_tz.gettz(timezone_string)
            except ImportError:
                # Last resort: try pytz
                import pytz

                tz = pytz.timezone(timezone_string)

        if tz is None:
            raise ValueError(f"Invalid timezone string: {timezone_string}")  # noqa: TRY301

    except (ValueError, KeyError, OSError) as e:
        # If we can't parse it as a named timezone, it might be a fixed offset like "UTC+10:00"
        # Try to create a timestamp with this timezone
        try:
            if sample_timestamp is None:
                ts = pd.Timestamp("2024-01-01").tz_localize(timezone_string)
            elif sample_timestamp.tz is not None:
                # Already tz-aware, use directly
                ts = sample_timestamp
            else:
                ts = sample_timestamp.tz_localize(timezone_string)
            # If successful, extract the offset
            offset = ts.utcoffset()
            if offset is not None:
                total_seconds = int(offset.total_seconds())
                sign = "+" if total_seconds >= 0 else "-"
                abs_seconds = abs(total_seconds)
                hours = abs_seconds // 3600
                minutes = (abs_seconds % 3600) // 60
                offset_string = f"{sign}{hours:02d}:{minutes:02d}"
                return (timezone_string, offset_string)
        except (ValueError, TypeError, KeyError):
            # Could not parse as fixed offset either
            pass
        raise ValueError(f"Could not parse timezone string '{timezone_string}': {e}") from e

    # Check if the timezone has DST transitions
    # We check offsets at different times of the year (winter and summer)
    # to detect if they differ
    if sample_timestamp is None:
        # Use two dates: one in winter (January) and one in summer (July)
        winter_ts = pd.Timestamp("2024-01-15 12:00:00").tz_localize(tz)
        summer_ts = pd.Timestamp("2024-07-15 12:00:00").tz_localize(tz)
    elif sample_timestamp.tz is not None:
        # sample_timestamp is already tz-aware, use directly
        winter_ts = sample_timestamp
        summer_ts = sample_timestamp + pd.DateOffset(months=6)
    else:
        # sample_timestamp is tz-naive, localize it
        winter_ts = sample_timestamp.tz_localize(tz)
        summer_ts = (sample_timestamp + pd.DateOffset(months=6)).tz_localize(tz)

    # Check offsets for DST
    try:
        winter_offset = winter_ts.utcoffset()
        summer_offset = summer_ts.utcoffset()

        if winter_offset != summer_offset:
            # Different offsets indicate DST
            raise NotImplementedError(  # noqa: TRY301
                f"Timezones with daylight saving time (DST) are not supported. "
                f"The timezone '{timezone_string}' has varying UTC offsets "
                f"(e.g., {winter_offset} in winter vs {summer_offset} in summer), "
                f"which is incompatible with NetCDF's static time encoding format "
                f"'time_units since ORIGIN +OFFSET'. "
                f"Please convert your data to a fixed UTC offset timezone "
                f"(e.g., 'UTC+10:00' or 'UTC-05:00') before saving to STF2 format.",
            )

    except NotImplementedError:
        # Re-raise NotImplementedError for DST
        raise
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        raise ValueError(f"Error checking timezone '{timezone_string}': {e}") from e

    # Fixed offset timezone - extract the offset
    offset = winter_offset
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    abs_seconds = abs(total_seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60
    offset_string = f"{sign}{hours:02d}:{minutes:02d}"

    return (timezone_string, offset_string)


def extract_utc_offset_string(timestamps_or_tz: pd.DatetimeIndex | pd.Timestamp | str | Any) -> str:
    """Extract UTC offset string from timestamps or timezone object.

    This is a utility function that extracts the UTC offset from timezone-aware
    timestamps or a timezone object and formats it consistently as "+HH:MM" or "-HH:MM".

    Args:
        timestamps_or_tz: Can be:
            - pd.DatetimeIndex (timezone-aware)
            - pd.Timestamp (timezone-aware)
            - Timezone string (e.g., "UTC+10:00", "US/Eastern")
            - Timezone object (from zoneinfo, pytz, dateutil)

    Returns:
        Formatted UTC offset string (e.g., "+00:00", "+10:00", "-05:00")

    Raises:
        ValueError: If input is timezone-naive or offset cannot be determined
        TypeError: If input type is not supported

    Examples:
        >>> import pandas as pd
        >>> timestamps = pd.date_range("2024-01-01", periods=3, tz="UTC+10:00")
        >>> extract_utc_offset_string(timestamps)
        '+10:00'

        >>> ts = pd.Timestamp("2024-01-01", tz="UTC-05:00")
        >>> extract_utc_offset_string(ts)
        '-05:00'

        >>> extract_utc_offset_string("UTC+05:30")
        '+05:30'

    Note:
        For timezones with DST, the offset will be based on the specific timestamp provided.
        For timezone strings without a specific timestamp, a sample date is used.
    """
    offset = None
    sample_ts = None

    # Handle different input types
    if isinstance(timestamps_or_tz, pd.DatetimeIndex):
        if len(timestamps_or_tz) == 0:
            raise ValueError("Cannot extract offset from empty DatetimeIndex")
        if timestamps_or_tz.tz is None:
            raise ValueError("DatetimeIndex is timezone-naive, cannot extract UTC offset")
        sample_ts = timestamps_or_tz[0]
        offset = sample_ts.utcoffset()

    elif isinstance(timestamps_or_tz, pd.Timestamp):
        if timestamps_or_tz.tz is None:
            raise ValueError("Timestamp is timezone-naive, cannot extract UTC offset")
        sample_ts = timestamps_or_tz
        offset = sample_ts.utcoffset()

    elif isinstance(timestamps_or_tz, str):
        # It's a timezone string, try to parse it and get the offset
        try:
            # Use detect_timezone_info to handle this
            _, offset_string = detect_timezone_info(pd.Timestamp("2024-01-15", tz=timestamps_or_tz))
            return offset_string  # noqa: TRY300
        except Exception as e:
            raise ValueError(f"Could not extract offset from timezone string '{timestamps_or_tz}': {e}") from e

    else:
        from datetime import (
            timezone,  # Note: I need to import. if I test isinstance for datetime.timezone, it throws an error. Weird.
        )
        from zoneinfo import ZoneInfo

        from dateutil import tz as dateutil_tz

        # test whether it's one of the timezone object (zoneinfo.ZoneInfo, pytz.timezone, dateutil.tz)
        if isinstance(timestamps_or_tz, (ZoneInfo, dateutil_tz.tzfile, dateutil_tz.tzoffset, timezone)):
            # Try to create a timestamp with this timezone
            try:
                sample_ts = pd.Timestamp("2024-01-15").tz_localize(timestamps_or_tz)
                offset = sample_ts.utcoffset()
            except Exception as e:
                raise TypeError(
                    f"Cannot extract UTC offset from type {type(timestamps_or_tz)}. "
                    f"Expected pd.DatetimeIndex, pd.Timestamp, timezone string, or timezone object. "
                    f"Error: {e}",
                ) from e
        else:
            raise TypeError(
                f"Cannot extract UTC offset from type {type(timestamps_or_tz)}. "
                f"Expected pd.DatetimeIndex, pd.Timestamp, timezone string, or timezone object, but got {type(timestamps_or_tz)}.",
            )

    # Format the offset
    if offset is None:
        raise ValueError("Could not determine UTC offset from input")

    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    abs_seconds = abs(total_seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60

    return f"{sign}{hours:02d}:{minutes:02d}"


def exportable_to_stf2(data: MdDatasetsType) -> bool:
    """Check if the dataset can be written to a netCDF file compliant with STF 2.0 specification.

    This method checks if the underlying xarray dataset or dataarray has the required dimensions and global attributes as specified by the STF 2.0 convention.

    Returns:
        bool: True if the dataset can be written to a STF 2.0 compliant netCDF file, False otherwise.
    """
    from efts_io.conventions import has_required_stf2_dimensions, has_required_variables_xr, mandatory_xarray_dimensions  # noqa: I001

    required_stf2_dimensions = has_required_stf2_dimensions(data, mandatory_xarray_dimensions)
    required_attributes = has_required_xarray_global_attributes(data)
    required_variables = has_required_variables_xr(data)
    # Check that station_ids are not strings though:
    if STATION_ID_DIMNAME not in data:  # must be because of above checks, but no harm in checking
        return False
    station_ids = data[STATION_ID_DIMNAME].values
    # it can be an object type of string or integer, so let's check:
    supported_types = (np.integer, np.bytes_, np.str_)
    if not issubclass(station_ids.dtype.type, supported_types):
        return False

    if TIME_DIMNAME not in data.coords:
        raise ValueError(
            f"Time dimension '{TIME_DIMNAME}' is required for STF 2.0 export, but not found in the dataset coordinates.",
        )
    # Check that the time dimension, if present, has a fixed-offset timezone (no DST)
    time_values = data[
        TIME_DIMNAME
    ]  # NOT .values, otherwise you may get integer values oddly enough. https://github.com/csiro-hydroinformatics/efts-io/issues/31#issuecomment-3981232548
    if len(time_values) > 0:
        try:
            # Detect timezone information from the time values
            tz_string, _ = detect_timezone_info(time_values)
            # Validate that the timezone doesn't have daylight saving time
            # Use .item() to extract scalar value from 0-d DataArray
            sample_ts = pd.Timestamp(time_values[0].item())
            validate_fixed_offset_timezone(tz_string, sample_ts)
        except NotImplementedError:
            # Timezone has DST, not supported for STF2 export
            return False
        except (ValueError, TypeError):
            # Error parsing timezone or timestamps - consider as not exportable
            return False

    # Check that lead_time coordinate does not contain zero (STF 2.0 convention §Description of Variables)
    if LEAD_TIME_DIMNAME in data.coords:
        lead_time_values = data[LEAD_TIME_DIMNAME].values
        if 0 in lead_time_values:
            return False

    return required_stf2_dimensions and required_attributes and required_variables


class TimeSeriesType(Enum):
    """Type of time series aggregation according to STF 2.0 conventions.

    This enumeration defines how time series data is aggregated or sampled,
    following the STF (Standard Time Format) 2.0 conventions for water forecasting netCDF files.

    Attributes:
        INSTANTANEOUS: Data recorded at a specific instant (e.g., stage height)
        ACCUMULATED: Data accumulated over the preceding time interval (e.g., rainfall)
        AVERAGED: Data averaged over the preceding time interval (e.g., flow, average temp)
        ACCUMULATED_FORECAST: Data accumulated since start of forecast (e.g., cumulative flow)
        POINT_IN_INTERVAL: Point value recorded in the preceding interval (e.g., max/min temperature)
        CLIMATOLOGY_INSTANTANEOUS: Climatology of instantaneous data
        CLIMATOLOGY_ACCUMULATED: Climatology of accumulated data
        CLIMATOLOGY_AVERAGED: Climatology of averaged data
        CLIMATOLOGY_ACCUMULATED_FORECAST: Climatology of forecast-accumulated data
        CLIMATOLOGY_POINT: Climatology of point-in-interval data

    Examples:
        >>> from efts_io.attributes import TimeSeriesType
        >>> ts_type = TimeSeriesType.ACCUMULATED
        >>> ts_type.code
        2
        >>> ts_type.description
        'accumulated over the preceding interval'
    """

    INSTANTANEOUS = (1, "instantaneous data")
    ACCUMULATED = (2, "accumulated over the preceding interval")
    AVERAGED = (3, "averaged over the preceding interval")
    ACCUMULATED_FORECAST = (4, "accumulated since start of forecast")
    POINT_IN_INTERVAL = (5, "point value recorded in the preceding interval")
    CLIMATOLOGY_INSTANTANEOUS = (11, "climatology data - instantaneous data")
    CLIMATOLOGY_ACCUMULATED = (12, "climatology data - accumulated over the preceding interval")
    CLIMATOLOGY_AVERAGED = (13, "climatology data - averaged over the preceding interval")
    CLIMATOLOGY_ACCUMULATED_FORECAST = (14, "climatology data - accumulated since start of forecast")
    CLIMATOLOGY_POINT = (15, "climatology data - point value recorded in the preceding interval")

    def __init__(self, code: int, description: str) -> None:
        """Initialize a TimeSeriesType with its numeric code and text description.

        Args:
            code: Numeric code defined by STF 2.0 conventions
            description: Human-readable description of the aggregation type
        """
        self.code = code
        self.description = description


class DataOriginType(Enum):
    """Type of data origin according to STF 2.0 conventions.

    This enumeration defines how the data was obtained or generated,
    following the STF (Standard Time Format) 2.0 conventions.

    Attributes:
        OBSERVED: Data observed directly from instruments (e.g., gauged rainfall)
        DERIVED: Data derived from observations through processing (e.g., AWAP rainfall)
        SIMULATED: Data simulated from historical observations (e.g., flow from GR4H with obs forcing)
        FORECAST: Data forecast/simulated from predictions (e.g., flow from GR4H with NWP forcing)

    Examples:
        >>> from efts_io.attributes import DataOriginType
        >>> origin = DataOriginType.OBSERVED
        >>> origin.code
        'obs'
        >>> origin.description
        'observed directly'
    """

    OBSERVED = ("obs", "observed directly")
    DERIVED = ("der", "derived from observations")
    SIMULATED = ("sim", "simulated from observations")
    FORECAST = ("fct", "simulated from forecasts")

    def __init__(self, code: str, description: str) -> None:
        """Initialize a DataOriginType with its string code and text description.

        Args:
            code: String code defined by STF 2.0 conventions
            description: Human-readable description of the data origin
        """
        self.code = code
        self.description = description


class LocationType(Enum):
    """Type of measurement location according to STF 2.0 conventions.

    This enumeration defines whether the measurement represents a point
    or an area-averaged value.

    Attributes:
        POINT: Point measurement (e.g., rain gauge, stream gauge)
        AREA: Area-averaged measurement (e.g., subcatchment area)

    Examples:
        >>> from efts_io.attributes import LocationType
        >>> loc = LocationType.POINT
        >>> loc.value
        'Point'
    """

    POINT = "Point"
    AREA = "Area"
