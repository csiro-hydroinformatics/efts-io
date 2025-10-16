"""Naming conventions for the EFTS netCDF file format."""

from datetime import datetime  # noqa: I001
from typing import Any, Dict, Iterable, List, Optional, Union

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
REALISATION_DIMNAME = "realisation"

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

hydro_varnames = ("rain", "pet", "q", "swe", "tmin", "tmax")
var_type = ("obs", "sim")
obs_hydro_varnames = tuple(f"{var}_{var_type[0]}" for var in hydro_varnames)
sim_hydro_varnames = tuple(f"{var}_{var_type[1]}" for var in hydro_varnames)
obs_hydro_varnames_qul = tuple(f"{x}_qul" for x in obs_hydro_varnames)
sim_hydro_varnames_qul = tuple(f"{x}_qul" for x in sim_hydro_varnames)
known_hydro_varnames = obs_hydro_varnames + sim_hydro_varnames + obs_hydro_varnames_qul + sim_hydro_varnames_qul

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

# We use a URL at a specific commit point, to be used as a file attribute.
# STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts/blob/d7d43a995fb5e459bcb894e09b7bb89de03e285c/docs/netcdf_for_water_forecasting.md"
# July 2025, set a new location/commit point:
STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts-io/blob/42ee35f0f019e9bad48b94914429476a7e8278dc/docs/netcdf_for_water_forecasting.md"


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


def get_default_dim_order() -> List[str]:
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
    index_id: Optional[int],
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


def has_required_stf2_dimensions(d: MdDatasetsType, mandatory_dimensions: Optional[Iterable[str]] = None) -> bool:
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


def check_stf_compliance(file_path: str) -> Dict[str, List[str]]:
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
    return name in obs_hydro_varnames_qul or name in sim_hydro_varnames_qul


def _extract_var_type(variable: Any) -> str:
    if _is_observation_variable(variable):
        return "obs"
    if _is_simulation_variable(variable):
        return "sim"
    if _is_quality_variable(variable):
        return "qul"
    return None


def _check_variable_attributes_obs(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> List[str]:
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
) -> List[str]:
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


def _check_variable_attributes_qul(
    variable: Any,
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> List[str]:
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
    required_attributes: Dict[str, type],
    missing_attributes_messages: List[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> List[str]:
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
    required_attributes: Dict[str, type],
    missing_attributes_messages: List[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> List[str]:
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
    required_attributes: Dict[str, type],
    missing_attributes_messages: List[str],
    error_threshold: AttributesErrorLevel = AttributesErrorLevel.NONE,
) -> List[str]:
    if _is_ncdf4_withattrs(variable):
        return _check_attrs_ncdataset(variable, required_attributes, missing_attributes_messages, error_threshold)
    else:  # noqa: RET505
        return _check_attrs_xr(variable, required_attributes, missing_attributes_messages, error_threshold)


def _check_variable_attributes(variable: Any) -> List[str]:
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
    if var_type == "qul":
        return _check_variable_attributes_qul(variable)

    return []


def check_hydrologic_variables(file_path: str) -> Dict[str, List[str]]:
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
) -> List[str]:
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
    if STATION_ID_DIMNAME in data:  # must be, but no harm in checking
        station_ids = data[STATION_ID_DIMNAME].values
        if not np.issubdtype(station_ids.dtype, np.integer):
            return False

    return required_stf2_dimensions and required_attributes and required_variables
