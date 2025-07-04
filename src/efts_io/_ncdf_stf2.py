"""Low level functions to write an xarray dataarray to disk in the sft conventions.

These are functions ported from a collection of utilities initially in https://bitbucket.csiro.au/projects/SF/repos/python_functions/browse/swift_utility/swift_io.py
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
import xarray as xr
from netCDF4 import Dataset


def write_nc_stf2(
    out_nc_file: str,
    data: xr.DataArray,
    var_type: int = 1,
    data_type: int = 3,
    stf_nc_vers: int = 2,
    ens: bool = False,  # noqa: FBT001, FBT002
    timestep:str="days",
    data_qual: Optional[xr.DataArray] = None,
    overwrite:bool=True, # noqa: FBT001, FBT002
    loc_info: Optional[Dict[str, Any]] = None,
    global_att: Optional[Dict[str, Any]] = None,
) -> None:

    intdata_type = "i4"
    #var_type    -   Integer specifying the variable, as follows:
    #                   1 - streamflow
    #                   2 - potential evapotranspiration
    #                   3 - rainfall
    #                   4 - snow water equivalent
    #                   5 - minimum temperature
    #                   6 - maximum temperature

    #data_type   -   Integer specifying the data type of the variable, as
    #                   follows:
    #                   1 - derived from observations
    #                   2 - forecast
    #                   3 - observed
    #                   4 - simulated

    n_stations = len(data["station"])
    if global_att is None:
        nc_title=""
        catchment=""
        inst="CSIRO Environment"
        comment=""
        source=""
    else:
        nc_title=global_att["nc_title"]
        catchment=global_att["catchment"]
        inst = global_att["inst"]
        comment = global_att["comment"]
        source = global_att["source"]

    station = np.arange(1, n_stations+1)
    if loc_info is None:
        station_id = np.arange(1, n_stations+1)
        station_name = [str(num) for num in station_id]
        subXCentroid = np.nan
        subYCentroid = np.nan
        subArea = np.nan
        other_station_id = ""
    else:
        station_id = loc_info["station_id"]
        station_name = loc_info["station_name"]
        subXCentroid = loc_info["subXCentroid"]
        subYCentroid = loc_info["subYCentroid"]
        subArea = loc_info["subArea"]
        other_station_id = loc_info["other_station_id"]

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
        raise ValueError(f"xr_open_dataset_fast has not been implemented for {timestep} unit")

    # Check if file exists
    if os.path.exists(out_nc_file):
        if not overwrite:
            raise FileExistsError(f"Warning: The file '{out_nc_file}' exists, so either set overwrite=True to overwrite or give new filename.")
        os.remove(out_nc_file)
        # print(f"Warning: The file '{out_nc_file}' has been overwritten.")

    # Create netcdf file
    ncfile = Dataset(out_nc_file, "w", format="NETCDF4")
    # Global Attributes
    #ncfile.description = "CCLIR forecasts"
    ncfile.history = "Created " + datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ncfile.title = nc_title
    ncfile.institution = inst
    ncfile.source = source
    ncfile.catchment = catchment
    ncfile.STF_convention_version = stf_nc_vers
    ncfile.STF_nc_spec = "https://wiki.csiro.au/display/wirada/NetCDF+for+SWIFT"
    ncfile.comment = comment

    #  station
    # --------------------
    ncfile.createDimension("station", n_stations)
    station_var = ncfile.createVariable("station", intdata_type, ("station",), fill_value=-9999)
    station_var[:] = station

    #  station_id
    station_id_var = ncfile.createVariable("station_id", intdata_type, ("station",), fill_value=-9999)
    station_id_var.setncattr("long_name", "station or node identification code")
    station_id_var[:] = station_id

    #  station_name
    ncfile.createDimension("strLen", 30)
    station_name_var = ncfile.createVariable("station_name", "c", ("station", "strLen"))
    station_name_var.setncattr("long_name", "station or node name")
    for s_i, stn_name in enumerate(station_name):
        char_stn_name = [" "] * 30  # 30 char length
        stn_name_30 = stn_name[:30]
        char_stn_name[:len(stn_name_30)] = stn_name_30
        station_name_var[s_i, :] = char_stn_name

    # additional station id e.g. BoM
    other_station_id_var = ncfile.createVariable("other_station_id", "c", ("station", "strLen"))
    other_station_id_var.setncattr("long_name", "other station id e.g. BoM")
    for s_i, stn_name in enumerate(other_station_id):
        char_stn_name = [" "] * 30  # 30 char length
        stn_name_30 = stn_name[:30]
        char_stn_name[:len(stn_name_30)] = stn_name_30
        other_station_id_var[s_i, :] = char_stn_name
    # coordinates, area
    # --------------------
    lat_var = ncfile.createVariable("lat", "f", ("station", ), fill_value=-9999)
    lat_var.setncattr("long_name", "latitude")
    lat_var.setncattr("units", "degrees_north")
    lat_var.setncattr("axis", "y")
    lat_var[:] = subYCentroid

    lon_var = ncfile.createVariable("lon", "f", ("station",), fill_value=-9999)
    lon_var.setncattr("long_name", "longitude")
    lon_var.setncattr("units", "degrees_east")
    lon_var.setncattr("axis", "x")
    lon_var[:] = subXCentroid

    area_var = ncfile.createVariable("area", "f", ("station",), fill_value=-9999)
    area_var[:] = subArea

    # lead time
    # ------------
    ncfile.createDimension("lead_time", len(data["lead_time"]))
    lt_var = ncfile.createVariable("lead_time", intdata_type, ("lead_time",), fill_value=-9999)
    lt_var.setncattr("standard_name", "lead time")
    lt_var.setncattr("long_name", "forecast lead time")
    lt_var.setncattr("units", "days since time")
    lt_var.setncattr("axis", "v")
    lt_var[:] = data["lead_time"].values

    # ensemble members
    # ------------------
    ncfile.createDimension("ens_member", len(data["ens_member"]))
    ens_mem_var = ncfile.createVariable("ens_member", intdata_type, ("ens_member",), fill_value=-9999)
    ens_mem_var.setncattr("standard_name", "ens_member")
    ens_mem_var.setncattr("long_name", "ensemble member")
    ens_mem_var.setncattr("units", "member id")
    ens_mem_var.setncattr("axis", "u")
    ens_mem_var[:] = np.arange(1, len(data["ens_member"])+1)

    # time
    # ------
    ncfile.createDimension("time", len(data["time"]))
    time_var = ncfile.createVariable("time", intdata_type, ("time",), fill_value=-9999)
    time_var.setncattr("standard_name", "time")
    time_var.setncattr("long_name", "time")
    time_var.setncattr("time_standard", "UTC+00:00")
    time_var.setncattr("axis", "t")

    #time_units_str = "days since {} 00:00:00".format(data.attrs["fcast_date"])
    fcast_date = data.attrs["fcast_date"]
    time_units_str = f"{timestep_str} since {fcast_date}"
    time_var.setncattr("units", time_units_str)
    time_var[:] = data["time"].values

    # Borrowing from create_empty_stfnc.m
    # Name Arrays
    v_type = ["q","pet","rain","swe","tmin","tmax","tave"]
    v_type_long = ["streamflow","potential evapotranspiration","rainfall","snow water equivalent","minimum temperature","maximum temperature","average temperature"]
    v_units = ["m3/s","mm","mm","mm","K","K","K"]
    v_ttype = [3,2,2,2,5,5,5]
    v_ttype_name = ["averaged over the preceding interval","accumulated over the preceding interval","accumulated over the preceding interval",
    "point value recorded in the preceding interval","point value recorded in the preceding interval","averaged over the preceding interval"]

    d_type = [None] * 4
    d_type_long = [None] * 4
    d_type[0] = "der"
    d_type_long[0] = "derived (from observations)"

    if int(stf_nc_vers) ==1:
        d_type[1] = "fcast"
        d_type_long[1] = "forecast"
    elif int(stf_nc_vers) ==2:  # noqa: PLR2004
        d_type[1] = "fct"
        d_type_long[1] = "forecast"
    else:
        raise ValueError("Version not recognised: Currently only version 1.X or 2.X are supported")

    d_type[2] = "obs"
    d_type_long[2] = "observed"
    d_type[3] = "sim"
    d_type_long[3] = "simulated"

    # change var_type and data_type to python based index starting from 0
    var_type = var_type-1
    data_type = data_type-1
    #print(f"data_type: {data_type}')
    # Create prescribed variable names
    if int(stf_nc_vers) ==1:
        var_name_s = f"{v_type[var_type]}_{d_type[data_type]}"
        var_name_l = f"{d_type_long[data_type]} {v_type_long[var_type]}"
        if ens:
            var_name_s = f"{var_name_s}_ens"
            var_name_l = f"{var_name_l} ensemble"
    else:
        var_name_attr = d_type[data_type]
        dat_type_description = d_type_long[data_type]
        if data_type in [0, 2]:
            #print("Obs")
            var_name_s = f"{v_type[var_type]}_obs"
            var_name_l = f"observed {v_type_long[var_type]}"
        else:
            # print("Sim")
            var_name_s = f"{v_type[var_type]}_sim"
            var_name_l = f"simulated {v_type_long[var_type]}"

    qsim_var = ncfile.createVariable(var_name_s, "f", ("time", "ens_member", "station", "lead_time"), fill_value=-9999)
    qsim_var.setncattr("standard_name", var_name_s)
    qsim_var.setncattr("long_name", var_name_l)
    qsim_var.setncattr("units", v_units[var_type])

    qsim_var.setncattr("type", v_ttype[var_type])
    qsim_var.setncattr("type_description", v_ttype_name[var_type])
    if int(stf_nc_vers) == 2:
        qsim_var.setncattr("dat_type", var_name_attr)
        qsim_var.setncattr("dat_type_description", dat_type_description)
        qsim_var.setncattr("location_type", "Point")
    else:
        qsim_var.setncattr("Location_type", "Point")

    qsim_var[:,:,:,:] = data.values[:]


    # Specify the quality variable
    if data_qual is not None:
        qu_var_name_s = f"{var_name_s}_qual"
        if int(stf_nc_vers) == 1:
            if data_type ==2:
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, "f", ("time", "station", "lead_time"), fill_value=-1)
                qsim_qual_var[:,:,:] = data_qual.values[:]
            else:
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, "f", ("time", "station"), fill_value=-1)
                qsim_qual_var[:,:] = data_qual.values[:]
        else:
            qsim_qual_var = ncfile.createVariable(qu_var_name_s, "f", ("time", "ens_member","station", "lead_time"), fill_value=-1)
            qsim_qual_var[:,:,:,:] = data_qual.values[:]

        qu_var_name_l = f"{var_name_l} data quality"

        qsim_qual_var.setncattr("standard_name", qu_var_name_s)
        qsim_qual_var.setncattr("long_name", qu_var_name_l)
        if "quality_code" in data_qual.attrs.keys():
            Quality_code  = data_qual.attrs["quality_code"]
        else:
            Quality_code  = "Quality codes"

        qsim_qual_var.setncattr("units", Quality_code)
        # Write data

    # close file
    ncfile.close()

