"""Low level functions to write an xarray dataarray to disk in the sft conventions.

These are functions ported from a collection of utilities initially in https://bitbucket.csiro.au/projects/SF/repos/python_functions/browse/swift_utility/swift_io.py
"""

import os  # noqa: I001
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from efts_io.conventions import (
    DAT_TYPE_ATTR_KEY,
    DAT_TYPE_DESCRIPTION_ATTR_KEY,
    LAT_VARNAME,
    LOCATION_TYPE_ATTR_KEY,
    LON_VARNAME,
    REALISATION_DIMNAME,
    STATION_ID_DIMNAME,
    STF_2_0_URL,
    TYPE_ATTR_KEY,
    TYPE_DESCRIPTION_ATTR_KEY,
    TYPES_CONVERTIBLE_TO_TIMESTAMP,
    AttributesErrorLevel,
    check_optional_variable_attributes,
    convert_to_datetime64_utc,
    has_required_xarray_global_attributes,
)

from netCDF4 import Dataset


class StfVariable(Enum):
    STREAMFLOW = 1
    POTENTIAL_EVAPOTRANSPIRATION = 2
    RAINFALL = 3
    SNOW_WATER_EQUIVALENT = 4
    MINIMUM_TEMPERATURE = 5
    MAXIMUM_TEMPERATURE = 6


class StfDataType(Enum):
    DERIVED_FROM_OBSERVATIONS = 1
    FORECAST = 2
    OBSERVED = 3
    SIMULATED = 4


def _create_cf_time_axis(data: xr.DataArray, timestep_str: str) -> tuple[np.ndarray, str, str]:
    """Create a CF-compliant time axis for the given xarray DataArray.

    Args:
        data (xr.DataArray): The input data array.
        timestep_str (str): The time step string (e.g., "days").

    Returns:
        tuple[np.ndarray, str, str]: A tuple containing the encoded time axis,
        the units string, and the calendar string.
    """
    from xarray.coding import times  # noqa: I001
    from efts_io.conventions import TIME_DIMNAME

    tt = data[TIME_DIMNAME].values
    if len(tt) == 0:
        raise ValueError("Cannot create CF time axis from empty data array.")
    origin = tt[0]
    # will be strict in the first instance, relax or expand later on as needed
    if not any(isinstance(origin, t) for t in TYPES_CONVERTIBLE_TO_TIMESTAMP):
        raise TypeError(
            f"Expected data[TIME_DIMNAME] to be of a type convertible to pd.Timestamp, got {type(origin)} instead.",
        )
    origin = convert_to_datetime64_utc(origin)
    dtimes = [convert_to_datetime64_utc(x) for x in tt]
    # NOTE: this is not quite what is suggested by the STF convention in the example string.
    # The below is closer to the the 8601 specifications, however we use space not 'T' for date/time separator
    # https://docs.digi.com/resources/documentation/digidocs/90001488-13/reference/r_iso_8601_date_format.htm
    iso_8601_origin = pd.Timestamp(origin).tz_localize("UTC")
    formatted_string = iso_8601_origin.strftime("%Y-%m-%d %H:%M:%S")
    timezone_offset = iso_8601_origin.strftime("%z")
    formatted_timezone_offset = f"{timezone_offset[:3]}:{timezone_offset[3:]}"
    formatted_string_with_tz = f"{formatted_string}{formatted_timezone_offset}"

    axis, units, calendar = times.encode_cf_datetime(
        dates=dtimes,  #: 'T_DuckArray',
        units=f"{timestep_str} since {formatted_string_with_tz}",  #: 'str | None' = None,
        calendar=None,  #: 'str | None' = None,
        dtype=None,  #: 'np.dtype | None' = None,
    )  # -> 'tuple[T_DuckArray, str, str]'
    # override times.encode_cf_datetime, which is varying
    # depending on the imput unit string and may not have the time zone, or a T separator.
    units = f"{timestep_str} since {formatted_string_with_tz}"
    return axis, units, calendar


def write_nc_stf2(
    out_nc_file: str,
    dataset: xr.Dataset,
    data: xr.DataArray,
    var_type: StfVariable = StfVariable.STREAMFLOW,
    data_type: StfDataType = StfDataType.OBSERVED,
    stf_nc_vers: int = 2,
    ens: bool = False,  # noqa: FBT001, FBT002
    timestep: str = "days",
    data_qual: Optional[xr.DataArray] = None,
    overwrite: bool = True,  # noqa: FBT001, FBT002
    # loc_info: Optional[Dict[str, Any]] = None,
    intdata_type: str = "i4",
) -> None:
    from efts_io.conventions import (  # noqa: I001
        X_VARNAME,
        Y_VARNAME,
        AREA_VARNAME,
        ELEVATION_VARNAME,
        AXIS_ATTR_KEY,
        CATCHMENT_ATTR_KEY,
        COMMENT_ATTR_KEY,
        ENS_MEMBER_DIMNAME,
        HISTORY_ATTR_KEY,
        INSTITUTION_ATTR_KEY,
        LEAD_TIME_DIMNAME,
        LONG_NAME_ATTR_KEY,
        SOURCE_ATTR_KEY,
        STANDARD_NAME_ATTR_KEY,
        STATION_DIMNAME,
        STATION_ID_VARNAME,
        STATION_NAME_VARNAME,
        STF_CONVENTION_VERSION_ATTR_KEY,
        STR_LEN_DIMNAME,
        TIME_DIMNAME,
        TIME_STANDARD_ATTR_KEY,
        TITLE_ATTR_KEY,
        UNITS_ATTR_KEY,
        is_subset_required_xarray_dimensions,
        mandatory_xarray_dimensions,
        mandatory_global_attributes,
        has_required_variables_xr,
        mandatory_varnames_xr,
        has_variable,
    )

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

    # Check that optional variables, if present, have the minimum attributes present.
    def _check_optional_var_attr(dataset: xr.Dataset, var_id: str) -> None:
        if has_variable(dataset, var_id):
            xrvar = dataset[var_id]
            check_optional_variable_attributes(xrvar, AttributesErrorLevel.ERROR)

    for var_id in (AREA_VARNAME, X_VARNAME, Y_VARNAME, ELEVATION_VARNAME):
        _check_optional_var_attr(dataset, var_id)

    var_type = var_type.value
    data_type = data_type.value

    n_stations = len(data[STATION_ID_DIMNAME])

    station = np.arange(1, n_stations + 1)

    # Retrieve arrays from expected variables in the input xarray dataarray `data`
    station_id = dataset[STATION_ID_VARNAME].values
    station_name = dataset[STATION_NAME_VARNAME].values
    sub_x_centroid = dataset[LON_VARNAME].values
    sub_y_centroid = dataset[LAT_VARNAME].values

    # NOTE: the original code had an "other_station_id" option, apparently storing some
    # identifiers from the Bureau of meteorology. For the time being, disable,
    # but initiate a discussion. See issue #9.
    # other_station_id = data["other_station_id"].values

    if timestep in ["weeks", "w", "wk", "week"]:
        timestep_str = "weeks"
    elif timestep in ["days", "d", "ds", "day"]:
        timestep_str = "days"
    elif timestep in ["hours", "h", "hr", "hour"]:
        timestep_str = "hours"
    elif timestep in ["minutes", "m", "min", "minute"]:
        timestep_str = "minutes"
    elif timestep in ["seconds", "s", "sec", "second"]:
        timestep_str = "seconds"
    else:
        raise ValueError(f"Unsupported or unrecognised time step unit: {timestep}")

    # Check if file exists
    if os.path.exists(out_nc_file):
        if not overwrite:
            raise FileExistsError(
                f"Warning: The file '{out_nc_file}' exists, so either set overwrite=True to overwrite or give new filename.",
            )
        os.remove(out_nc_file)
        # print(f"Warning: The file '{out_nc_file}' has been overwritten.")

    # Create netcdf file
    ncfile = Dataset(out_nc_file, "w", format="NETCDF4")
    # Global Attributes
    # ncfile.description = "CCLIR forecasts"
    ncfile.title = dataset.attrs.get(TITLE_ATTR_KEY, "")  # = nc_title
    ncfile.institution = dataset.attrs.get(INSTITUTION_ATTR_KEY, "")  # = inst
    ncfile.source = dataset.attrs.get(SOURCE_ATTR_KEY, "")  # = source
    ncfile.catchment = dataset.attrs.get(CATCHMENT_ATTR_KEY, "")  # = catchment
    ncfile.STF_convention_version = dataset.attrs.get(STF_CONVENTION_VERSION_ATTR_KEY, "")  # = stf_nc_vers
    ncfile.STF_nc_spec = STF_2_0_URL  # we do not transfer the spec version, this code determines it.
    ncfile.comment = dataset.attrs.get(COMMENT_ATTR_KEY, "")  # = comment
    ncfile.history = dataset.attrs.get(HISTORY_ATTR_KEY, "")
    # = "Created " + datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    #  station
    # --------------------
    ncfile.createDimension(STATION_DIMNAME, n_stations)
    station_var = ncfile.createVariable(STATION_DIMNAME, intdata_type, (STATION_DIMNAME,), fill_value=-9999)
    station_var[:] = station

    #  station_id

    # we check that station_id can be safely stored as int32
    # I add this deliberately as a check to avoid possibly silent data corruption as observed in
    # https://github.com/csiro-hydroinformatics/efts-io/issues/17
    if intdata_type == "i4":
        max_station_id = np.max(station_id)
        min_station_id = np.min(station_id)
        if not np.issubdtype(type(max_station_id), np.integer) or not np.issubdtype(type(min_station_id), np.integer):
            raise TypeError("station_id values must be integers to be stored in STF2.0 format.")
        if max_station_id > np.iinfo(np.int32).max or min_station_id < np.iinfo(np.int32).min:
            raise OverflowError(
                f"station_id values must be in the int32 range [{np.iinfo(np.int32).min}, {np.iinfo(np.int32).max}] to be stored in STF2.0 format.",
            )

    station_id_var = ncfile.createVariable(STATION_ID_VARNAME, intdata_type, (STATION_DIMNAME,), fill_value=-9999)
    station_id_var.setncattr(LONG_NAME_ATTR_KEY, "station or node identification code")
    station_id_var[:] = station_id

    #  station_name
    ncfile.createDimension(STR_LEN_DIMNAME, 30)
    station_name_var = ncfile.createVariable(STATION_NAME_VARNAME, "c", (STATION_DIMNAME, STR_LEN_DIMNAME))
    station_name_var.setncattr(LONG_NAME_ATTR_KEY, "station or node name")
    for s_i, stn_name in enumerate(station_name):
        char_stn_name = [" "] * 30  # 30 char length
        stn_name_30 = stn_name[:30]
        char_stn_name[: len(stn_name_30)] = stn_name_30
        station_name_var[s_i, :] = char_stn_name

    # additional station id e.g. BoM
    # other_station_id_var = ncfile.createVariable("other_station_id", "c", (STATION_DIMNAME, STR_LEN_DIMNAME))
    # other_station_id_var.setncattr(LONG_NAME_ATTR_KEY, "other station id e.g. BoM")
    # for s_i, stn_name in enumerate(other_station_id):
    #     char_stn_name = [" "] * 30  # 30 char length
    #     stn_name_30 = stn_name[:30]
    #     char_stn_name[: len(stn_name_30)] = stn_name_30
    #     other_station_id_var[s_i, :] = char_stn_name
    # coordinates, area
    # --------------------
    lat_var = ncfile.createVariable(LAT_VARNAME, "f", (STATION_DIMNAME,), fill_value=-9999)
    lat_var.setncattr(LONG_NAME_ATTR_KEY, "latitude")
    lat_var.setncattr(UNITS_ATTR_KEY, "degrees_north")
    lat_var.setncattr(AXIS_ATTR_KEY, "y")
    lat_var[:] = sub_y_centroid

    lon_var = ncfile.createVariable(LON_VARNAME, "f", (STATION_DIMNAME,), fill_value=-9999)
    lon_var.setncattr(LONG_NAME_ATTR_KEY, "longitude")
    lon_var.setncattr(UNITS_ATTR_KEY, "degrees_east")
    lon_var.setncattr(AXIS_ATTR_KEY, "x")
    lon_var[:] = sub_x_centroid

    def add_optional_variables(data: xr.DataArray, ncfile: Dataset, var_id: str) -> None:
        if has_variable(data, var_id):
            ncvar_type = "f"
            xrvar = data[var_id]
            opt_nc_var = ncfile.createVariable(var_id, ncvar_type, (STATION_DIMNAME,), fill_value=-9999)
            opt_nc_var[:] = xrvar.values
            for x in (STANDARD_NAME_ATTR_KEY, LONG_NAME_ATTR_KEY, UNITS_ATTR_KEY):
                opt_nc_var.setncattr(x, xrvar.attrs[x])

    for var_id in (AREA_VARNAME, X_VARNAME, Y_VARNAME, ELEVATION_VARNAME):
        add_optional_variables(dataset, ncfile, var_id)

    dimensions_order = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
    # expand and reorder if necessary the dimensions of the array.
    # In part see feature request https://github.com/csiro-hydroinformatics/efts-io/issues/14
    data = make_ready_for_saving(data, dataset, dimensions_order)

    # lead time
    # ------------
    ncfile.createDimension(LEAD_TIME_DIMNAME, len(data[LEAD_TIME_DIMNAME]))
    lt_var = ncfile.createVariable(LEAD_TIME_DIMNAME, intdata_type, (LEAD_TIME_DIMNAME,), fill_value=-9999)
    lt_var.setncattr(STANDARD_NAME_ATTR_KEY, "lead time")
    lt_var.setncattr(LONG_NAME_ATTR_KEY, "forecast lead time")
    lt_var.setncattr(UNITS_ATTR_KEY, "days since time")
    lt_var.setncattr(AXIS_ATTR_KEY, "v")
    lt_var[:] = data[LEAD_TIME_DIMNAME].values

    # ensemble members
    # ------------------
    ncfile.createDimension(ENS_MEMBER_DIMNAME, len(data[REALISATION_DIMNAME]))
    ens_mem_var = ncfile.createVariable(ENS_MEMBER_DIMNAME, intdata_type, (ENS_MEMBER_DIMNAME,), fill_value=-9999)
    ens_mem_var.setncattr(STANDARD_NAME_ATTR_KEY, ENS_MEMBER_DIMNAME)
    ens_mem_var.setncattr(LONG_NAME_ATTR_KEY, "ensemble member")
    ens_mem_var.setncattr(UNITS_ATTR_KEY, "member id")
    ens_mem_var.setncattr(AXIS_ATTR_KEY, "u")
    ens_mem_var[:] = np.arange(1, len(data[REALISATION_DIMNAME]) + 1)

    # time
    # ------
    ncfile.createDimension(TIME_DIMNAME, len(data[TIME_DIMNAME]))
    time_var = ncfile.createVariable(TIME_DIMNAME, intdata_type, (TIME_DIMNAME,), fill_value=-9999)
    time_var.setncattr(STANDARD_NAME_ATTR_KEY, TIME_DIMNAME)
    time_var.setncattr(LONG_NAME_ATTR_KEY, TIME_DIMNAME)
    time_var.setncattr(TIME_STANDARD_ATTR_KEY, "UTC+00:00")
    time_var.setncattr(AXIS_ATTR_KEY, "t")

    # time_units_str = "days since {} 00:00:00".format(data.attrs["fcast_date"])
    axis_values, time_units_str, _ = _create_cf_time_axis(data, timestep_str)
    time_var.setncattr(UNITS_ATTR_KEY, time_units_str)
    time_var[:] = axis_values

    # Borrowing from create_empty_stfnc.m
    # Name Arrays
    v_type = ["q", "pet", "rain", "swe", "tmin", "tmax", "tave"]
    v_type_long = [
        "streamflow",
        "potential evapotranspiration",
        "rainfall",
        "snow water equivalent",
        "minimum temperature",
        "maximum temperature",
        "average temperature",
    ]
    v_units = ["m3/s", "mm", "mm", "mm", "K", "K", "K"]
    v_ttype = [3, 2, 2, 2, 5, 5, 5]
    v_ttype_name = [
        "averaged over the preceding interval",
        "accumulated over the preceding interval",
        "accumulated over the preceding interval",
        "point value recorded in the preceding interval",
        "point value recorded in the preceding interval",
        "averaged over the preceding interval",
    ]

    d_type = [None] * 4
    d_type_long = [None] * 4
    d_type[0] = "der"
    d_type_long[0] = "derived (from observations)"

    if int(stf_nc_vers) == 1:
        d_type[1] = "fcast"
        d_type_long[1] = "forecast"
    elif int(stf_nc_vers) == 2:  # noqa: PLR2004
        d_type[1] = "fct"
        d_type_long[1] = "forecast"
    else:
        raise ValueError("Version not recognised: Currently only version 1.X or 2.X are supported")

    d_type[2] = "obs"
    d_type_long[2] = "observed"
    d_type[3] = "sim"
    d_type_long[3] = "simulated"

    # change var_type and data_type to python based index starting from 0
    var_type = var_type - 1
    data_type = data_type - 1
    # print(f"data_type: {data_type}')
    # Create prescribed variable names
    if int(stf_nc_vers) == 1:
        var_name_s = f"{v_type[var_type]}_{d_type[data_type]}"
        var_name_l = f"{d_type_long[data_type]} {v_type_long[var_type]}"
        if ens:
            var_name_s = f"{var_name_s}_ens"
            var_name_l = f"{var_name_l} ensemble"
    else:
        var_name_attr = d_type[data_type]
        dat_type_description = d_type_long[data_type]
        if data_type in [0, 2]:
            # print("Obs")
            var_name_s = f"{v_type[var_type]}_obs"
            var_name_l = f"observed {v_type_long[var_type]}"
        else:
            # print("Sim")
            var_name_s = f"{v_type[var_type]}_sim"
            var_name_l = f"simulated {v_type_long[var_type]}"

    qsim_var = ncfile.createVariable(
        var_name_s,
        "f",
        dimensions_order,
        fill_value=-9999,
    )
    qsim_var.setncattr(STANDARD_NAME_ATTR_KEY, var_name_s)
    qsim_var.setncattr(LONG_NAME_ATTR_KEY, var_name_l)
    qsim_var.setncattr(UNITS_ATTR_KEY, v_units[var_type])

    qsim_var.setncattr(TYPE_ATTR_KEY, v_ttype[var_type])
    qsim_var.setncattr(TYPE_DESCRIPTION_ATTR_KEY, v_ttype_name[var_type])
    if int(stf_nc_vers) == 2:  # noqa: PLR2004
        qsim_var.setncattr(DAT_TYPE_ATTR_KEY, var_name_attr)
        qsim_var.setncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY, dat_type_description)
        qsim_var.setncattr(LOCATION_TYPE_ATTR_KEY, "Point")
    else:
        qsim_var.setncattr(LOCATION_TYPE_ATTR_KEY, "Point")

    qsim_var[:, :, :, :] = data.values[:]

    # Specify the quality variable
    if data_qual is not None:
        qu_var_name_s = f"{var_name_s}_qual"
        if int(stf_nc_vers) == 1:
            if data_type == 2:  # noqa: PLR2004
                qsim_qual_var = ncfile.createVariable(
                    qu_var_name_s,
                    "f",
                    (TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME),
                    fill_value=-1,
                )
                qsim_qual_var[:, :, :] = data_qual.values[:]
            else:
                qsim_qual_var = ncfile.createVariable(
                    qu_var_name_s,
                    "f",
                    (TIME_DIMNAME, STATION_DIMNAME),
                    fill_value=-1,
                )
                qsim_qual_var[:, :] = data_qual.values[:]
        else:
            qsim_qual_var = ncfile.createVariable(
                qu_var_name_s,
                "f",
                (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME),
                fill_value=-1,
            )
            qsim_qual_var[:, :, :, :] = data_qual.values[:]

        qu_var_name_l = f"{var_name_l} data quality"

        qsim_qual_var.setncattr(STANDARD_NAME_ATTR_KEY, qu_var_name_s)
        qsim_qual_var.setncattr(LONG_NAME_ATTR_KEY, qu_var_name_l)
        quality_code = data_qual.attrs.get("quality_code", "Quality codes")

        qsim_qual_var.setncattr(UNITS_ATTR_KEY, quality_code)
        # Write data

    # close file
    ncfile.close()


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
