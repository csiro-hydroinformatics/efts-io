"""Handling of EFTS netCDF variables definitions."""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from efts_io._internals import create_data_variable
from efts_io.attributes import create_var_attribute_definition
from efts_io.conventions import (
    ensemble_member_dim_name,
    lead_time_dim_name,
    stations_dim_name,
)
from efts_io.dimensions import _create_nc_dims


#' Create a variable definition
#'
#' Create a variable definition usable by the function \code{\link{create_efts_variables}} to create netCDF variables.
#'
#' @param name variable name
#' @param longname variable long name
#' @param units variable units
#' @param missval value code for missing data
#' @param precision precision
#' @param dim_type dimension type (EFTS integer code)
#' @param var_attribute list of attributes for the netCDF variable to create
#' @export
#' @return a list
#' @examples
#' var_def = create_variable_definition(name='rain_der',
#'   longname='Rainfall ensemble forecast derived from some prediction', units='mm',
#'   missval=-9999.0, precision='double', var_attribute=list(type=2L,
#'     description="accumulated over the preceding interval",
#'     dat_type = "der", dat_type_description="AWAP data interpolated from observations",
#'     location_type = "Point"))
def create_variable_definition(
    name: str,
    longname: str = "",
    units: str = "mm",
    missval: float = -9999.0,
    precision: str = "double",
    dim_type: str = "4",
    var_attribute: Optional[str] = None,
) -> dict[str, Any]:
    """Create a variable definition."""
    if var_attribute is None:
        var_attribute = create_var_attribute_definition()
    return {
        "name": name,
        "longname": longname,
        "units": units,
        "dim_type": dim_type,
        "missval": missval,
        "precision": precision,
        "attributes": var_attribute,
    }


# #' Create a variables definition data frame
# #'
# #' Create a variable definition usable by the function \code{\link{create_variable_definitions}}
# #' to create netCDF variables. The use of this function is not compulsory to create a EFTS
# #' netCDF schema, just offered as a convenience.
# #'
# #' @param variable_names character vector, names of the variables
# #' @param long_names character vector, long names of the variables (defaults to variable_names if missing)
# #' @param standard_names character vector, standard names of the variables (optional, defaults to variable_names)
# #' @param units character vector, units for the variable(s)
# #' @param missval numeric vector, missing value code(s) for the variable(s)
# #' @param precision character vector, precision of the variables
# #' @param dimensions character or integer vector, number of dimensions each variable (2, 3 or 4)
# #' @param var_attributes a list of named attributes. See \code{\link{create_var_attribute_definition}}
# #' @export
# #' @return a data frame suitable for \code{\link{create_variable_definition}}
# #' @seealso See
# #'    \code{\link{create_variable_definition}} and \code{\link{create_efts}} for examples
# create_variable_definition_dataframe(variable_names, long_names = variable_names, standard_names = variable_names, units = "mm", missval = -9999.0,
#   precision = "double", dimensions = 4L, var_attributes = create_var_attribute_definition()) {
#   stopifnot(is.character(variable_names))
#   varsDef = data.frame(name = variable_names, stringsAsFactors = FALSE)
#   varsDef$longname = long_names
#   varsDef$standard_name = standard_names
#   varsDef$units = units
#   varsDef$missval = missval
#   varsDef$precision = precision
#   varsDef$dimensions = as.integer(dimensions)

#   va = data.frame(var_attributes, stringsAsFactors = FALSE)
#   if(nrow(va) < nrow(varsDef)) {
#     va = va[ rep(1:nrow(va), length.out=nrow(varsDef)), ]
#   }

#   varsDef = cbind(varsDef, va)
#   rownames(varsDef) = varsDef$name
#   return(varsDef)
# }


#' Provide a template definition of optional geolocation variables
#'
#' Provide a template definition of optional geolocation and geographic variables x, y, area and elevation.
#' See \url{https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md#optional-variables}.
#'
#' @export
#' @return a data frame
#' @seealso See
#'    \code{\link{create_variable_definition}} and \code{\link{create_efts}} for examples
#' @export
def default_optional_variable_definitions_v2_0() -> pd.DataFrame:
    """Provide a template definition of optional geolocation variables."""
    return pd.DataFrame.from_dict(
        {
            "name": ["x", "y", "area", "elevation"],
            "longname": [
                "easting from the GDA94 datum in MGA Zone 55",
                "northing from the GDA94 datum in MGA Zone 55",
                "catchment area",
                "station elevation above sea level",
            ],
            "standard_name": [
                "northing_GDA94_zone55",
                "easting_GDA94_zone55",
                "area",
                "elevation",
            ],
            "units": ["", "", "km^2", "m"],
            "missval": [np.nan, np.nan, -9999.0, -9999.0],
            "precision": np.repeat("float", 4),
        },
    )


# ########################################
# # Below are functions not exported
# ########################################


#' Create variable definitions from a data frame
#'
#' Given a data frame as input, create a list of variable definitions usable by the function \code{\link{create_efts_variables}} to create netCDF variables.
#'
#' @param dframe a data frame, one line is one variable definition. Must have at least the following column names: 'name', 'longname', 'units', 'missval', 'precision', 'type', 'type_description', 'location_type'
#' @export
#' @return a list of length equal to the number of rows in the input data frame
#' @seealso See
#'    \code{\link{create_efts}} for examples
#' @examples
#' varsDef = data.frame(name=letters[1:3], stringsAsFactors=FALSE)
#' varsDef$longname=paste('long name for', varsDef$name)
#' varsDef$units='mm'
#' varsDef$missval=-999.0
#' varsDef$precision='double'
#' varsDef$type=2
#' varsDef$type_description='accumulated over the previous time step'
#' varsDef$location_type='Point'
#' str(create_variable_definitions(varsDef))
#'
def create_variable_definitions(dframe: pd.DataFrame) -> List[Dict[str, Any]]:
    """Create variable definitions from a data frame."""
    in_names = dframe.columns
    non_opt_attr = ["name", "longname", "units", "missval", "precision", "dimensions"]
    varargs_attr = [x for x in in_names if x not in non_opt_attr]

    def f(var_def: Dict[str, Any]):  # noqa: ANN202
        return create_variable_definition(
            name=var_def["name"],
            longname=var_def["longname"],
            units=var_def["units"],
            missval=var_def["missval"],
            precision=var_def["precision"],
            dim_type=var_def["dimensions"],
            var_attribute=var_def[varargs_attr],
        )

    # dframe[['rownum']] = 1:nrow(dframe)
    # r = plyr::dlply(.data = dframe, .variables = "rownum", .fun = f)
    variables_defs: Dict = dframe.apply(lambda x: f(x), axis=1)
    res = {v["name"]: v for k, v in variables_defs.items()}
    return res


def create_mandatory_vardefs(
    station_dim: str,
    str_dim: str,
    ensemble_dim: str,
    lead_time_dim: str,
    lead_time_tstep: str = "hours",
) -> Dict[str, Dict[str, Any]]:
    """Create mandatory variable definitions."""
    # https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md#mandatory-variables
    # float time(time)
    # int station_id(station)
    # char station_name(strLen, station)
    # int ens_member(ens_member)
    # float lead_time(lead_time)
    # float lat (station)
    # float lon (station)
    import xarray as xr

    # stations_dim_name,
    # lead_time_dim_name,
    # time_dim_name,
    # ensemble_member_dim_name,
    # str_length_dim_name,

    station_id_variable = xr.Variable(
        dims=[stations_dim_name],
        data=station_dim[1],
        encoding={"_FillValue": None},
        attrs={
            "longname": station_dim[2]["longname"],
            "units": "",
            "missval": None,
            "precision": "integer",
        },
    )
    station_names_dim_variable = xr.Variable(
        dims=[str_dim[0], stations_dim_name],
        # That was not intuitive to create this empty array. Not entirely sure this is what we want.
        data=np.empty_like(
            prototype=b"", shape=(len(str_dim[1]), len(station_dim[1])), dtype=np.bytes_
        ),
        encoding={"_FillValue": None},
        attrs={
            "longname": "station or node name",
            "units": "",
            "missval": None,
            "precision": "char",
        },
    )
    ensemble_member_id_variable = xr.Variable(
        dims=[ensemble_member_dim_name],
        data=ensemble_dim[1],
        encoding={"_FillValue": None},
        attrs={
            "longname": ensemble_dim[2]["longname"],
            "units": "",
            "missval": None,
            "precision": "integer",
        },
    )
    lead_time_dim_variable = xr.Variable(
        dims=[lead_time_dim_name],
        data=lead_time_dim[1],
        encoding={"_FillValue": None},
        attrs={
            "longname": lead_time_dim[2]["longname"],
            "units": lead_time_tstep + " since time",
            "missval": None,
            "precision": "integer",
        },
    )
    latitude_dim_variable = xr.Variable(
        dims=[stations_dim_name],
        data=np.empty_like(station_dim[1], dtype=float),
        encoding={"_FillValue": -9999.0},
        attrs={
            "longname": "latitude",
            "units": "degrees north",
            "missval": -9999.0,
            "precision": "float",
        },
    )
    longitude_dim_variable = xr.Variable(
        dims=[stations_dim_name],
        data=np.empty_like(station_dim[1], dtype=float),
        encoding={"_FillValue": -9999.0},
        attrs={
            "longname": "longitude",
            "units": "degrees east",
            "missval": -9999.0,
            "precision": "float",
        },
    )

    return {
        "station_ids_var": station_id_variable,
        "station_names_var": station_names_dim_variable,
        "ensemble_var": ensemble_member_id_variable,
        "lead_time_var": lead_time_dim_variable,
        "latitude_var": latitude_dim_variable,
        "longitude_var": longitude_dim_variable,
    }


def create_optional_vardefs(
    station_dim: str, vars_def: Optional[pd.DataFrame] = None
) -> pd.Series:
    """Create optional variable definitions."""
    if vars_def is None:
        vars_def = default_optional_variable_definitions_v2_0()

    # https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md#mandatory-variables
    # vars_def$rownum = 1:nrow(vars_def)
    def f(vd: Dict):  # noqa: ANN202
        return {
            "name": vd["name"],
            "units": vd["units"],
            "dim": list(station_dim),
            "missval": vd["missval"],
            "longname": vd["longname"],
            "prec": vd["precision"],
        }

    return vars_def.apply(lambda x: f(x), axis=1)


#' Create netCDF variables according to the definition
#'
#' Create netCDF variables according to the definition
#'
#' @param data_var_def a list, with each item itself a list suitable as a variable definition argument to create_data_variable
#' @param time_dim_info a list with the units and values defining the time dimension of the data set
#' @param num_stations number of (gauging) stations identifying points in the data set
#' @param lead_length length of the lead forecasting time series.
#' @param ensemble_length number of ensembles, i.e. number of forecasts for each point on the main time axis of the data set
#' @param optional_vars a data frame defining optional netCDF variables. For a templated default see
#' \code{\link{default_optional_variable_definitions_v2_0}} and
#' \url{https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md#optional-variables}
#' @param lead_time_tstep string specifying the time step of the forecast lead length.
#' @seealso See
#'    \code{\link{create_efts}} for examples
def create_efts_variables(
    data_var_def: Dict,
    time_dim_info: Dict,
    num_stations: int,
    lead_length: int,
    ensemble_length: int,
    optional_vars: Optional[pd.DataFrame],
    lead_time_tstep: str,
) -> Dict[str, Any]:
    """Create netCDF variables according to the definition."""
    efts_dims = _create_nc_dims(
        time_dim_info=time_dim_info,
        num_stations=num_stations,
        lead_length=lead_length,
        ensemble_length=ensemble_length,
    )

    time_dim = efts_dims["time_dim"]
    lead_time_dim = efts_dims["lead_time_dim"]
    station_dim = efts_dims["station_dim"]
    str_dim = efts_dims["str_dim"]
    ensemble_dim = efts_dims["ensemble_dim"]

    mandatory_var_ncdefs = create_mandatory_vardefs(
        station_dim,
        str_dim,
        ensemble_dim,
        lead_time_dim,
        lead_time_tstep,
    )
    variables_metadata = mandatory_var_ncdefs
    if optional_vars is not None:
        optional_var_ncdefs = create_optional_vardefs(
            station_dim,
            vars_def=optional_vars,
        )
        # TODO if not native to ncdf4: check name clashes
        # already_defs = names(variables)
        variables_metadata = variables_metadata.update(optional_var_ncdefs)

    unknown_dims = [
        x for x in data_var_def.values() if x["dim_type"] not in ["2", "3", "4"]
    ]
    if len(unknown_dims) > 0:
        raise ValueError(
            "Invalid dimension specifications for "
            + len(unknown_dims)
            + " variables. Only supported are characters 2, 3, 4",
        )

    ens_fcast_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "4"]
    ens_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "3"]
    point_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "2"]

    variables = {}
    variables["metadatavars"] = variables_metadata

    data_variables = {}
    data_variables.update(
        {
            x["name"]: create_data_variable(
                x,
                [lead_time_dim, station_dim, ensemble_dim, time_dim],
            )
            for x in ens_fcast_data_var_def
        },
    )
    data_variables.update(
        {
            x["name"]: create_data_variable(x, [station_dim, ensemble_dim, time_dim])
            for x in ens_data_var_def
        },
    )
    data_variables.update(
        {
            x["name"]: create_data_variable(x, [station_dim, time_dim])
            for x in point_data_var_def
        },
    )
    variables["datavars"] = data_variables

    return variables
