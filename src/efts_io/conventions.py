"""Naming conventions for the EFTS netCDF file format."""

from datetime import datetime
from typing import Any, Iterable, List, Optional, Union

# import netCDF4 as nc
import numpy as np
import pandas as pd
import xarray as xr

ConvertibleToTimestamp = Union[str, datetime, np.datetime64, pd.Timestamp]
"""Definition of a 'type' for type hints.
"""


TIME_DIMNAME = "time"
STATION_DIMNAME = "station"
ENS_MEMBER_DIMNAME = "ens_member"
LEAD_TIME_DIMNAME = "lead_time"
STR_LEN_DIMNAME = "strLen"

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

conventional_varnames = [
    STATION_DIMNAME,
    LEAD_TIME_DIMNAME,
    TIME_DIMNAME,
    ENS_MEMBER_DIMNAME,
    STR_LEN_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    LAT_VARNAME,
    LON_VARNAME,
    X_VARNAME,
    Y_VARNAME,
    AREA_VARNAME,
    ELEVATION_VARNAME,
]

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

STF_2_0_URL = "https://github.com/csiro-hydroinformatics/efts/blob/d7d43a995fb5e459bcb894e09b7bb89de03e285c/docs/netcdf_for_water_forecasting.md"


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
mandatory_xarray_dimensions = [TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, ENS_MEMBER_DIMNAME]

mandatory_varnames = [
    TIME_DIMNAME,
    STATION_DIMNAME,
    LEAD_TIME_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    ENS_MEMBER_DIMNAME,
    LAT_VARNAME,
    LON_VARNAME,
]


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
    # Have to disable using directly netCDF4 for now due to issue #4
    return False
    # return isinstance(d, nc.Dataset)


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
        return set(d.dims.keys()) == set(mandatory_dimensions)


def has_required_stf2_dimensions(d: MdDatasetsType) -> bool:
    return _has_required_dimensions(d, mandatory_netcdf_dimensions)


def has_required_xarray_dimensions(d: MdDatasetsType) -> bool:
    return _has_required_dimensions(d, mandatory_xarray_dimensions)


def _has_all_members(tested: Iterable[str], reference: Iterable[str]) -> bool:
    r = set(reference)
    return set(tested).intersection(r) == r


def has_required_global_attributes(d: MdDatasetsType) -> bool:
    if _is_nc_dataset(d):
        a = d.ncattrs()
        tested = set(a)
    else:
        a = d.attrs.keys()
        tested = set(a)
    return _has_all_members(tested, mandatory_global_attributes)


def has_required_variables(d: MdDatasetsType) -> bool:
    a = d.variables.keys()
    tested = set(a)
    # Note: even if xarray, we do not need to check for the 'data_vars' attribute here.
    # a = d.data_vars.keys()
    # tested = set(a)
    return _has_all_members(tested, mandatory_varnames)
