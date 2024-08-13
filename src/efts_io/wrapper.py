import os
from typing import Any, Dict, List, Union

import numpy as np
import pandas as pd
import xarray as xr

from efts_io.conventions import *
from efts_io.variables import create_efts_variables, create_variable_definitions


def _byte_to_string(x: Any):
    if isinstance(x, int):
        if x > 255 or x < 0:
            raise ValueError("Integer value to bytes: must be in range [0-255]")
        x = x.to_bytes(1, "little")
    if not isinstance(x, bytes):
        raise ValueError(f"Cannot cast type {type(x)} to bytes")
    return str(x, encoding="UTF-8")


def _byte_array_to_string(x: np.ndarray):
    return "".join([_byte_to_string(s) for s in x])


def _byte_stations_to_str(byte_names: np.ndarray):
    return np.array([_byte_array_to_string(x) for x in byte_names])


def _cftime_to_pdtstamp(t, tz_str):
    return pd.Timestamp(t.isoformat(), tz=tz_str)


_ats = np.vectorize(_cftime_to_pdtstamp)


def cftimes_to_pdtstamps(cftimes, tz_str):
    return _ats(cftimes, tz_str)


def _first_where(condition):
    x = np.where(condition)[0]
    if len(x) < 1:
        raise Exception("first_where: Invalid condition, no element is true")
    return x[0]


class EftsDataSet:
    # Reference class convenient for access to a Ensemble Forecast Time Series in netCDF file.
    # Description
    # Reference class convenient for access to a Ensemble Forecast Time Series in netCDF file.

    # Fields
    # time_dim
    # a cached POSIXct vector, the values for the time dimension of the data set.

    # time_zone
    # the time zone for the time dimensions of this data set.

    # identifiers_dimensions
    # a cache, list of values of the primary data identifiers; e.g. station_name or station_id

    # stations_varname
    # name of the variable that stores the names of the stations for this data set.

    def __init__(self, data: Union[str, xr.Dataset]):
        from xarray.coding import times

        self.time_dim = None
        self.time_zone = "UTC"
        self.stations_dim_name = "station"
        self.stations_varname = "station_id"
        self.lead_time_dim_name = "lead_time"
        self.ensemble_member_dim_name = "ens_member"
        self.identifiers_dimensions = list()
        if isinstance(data, str):
            # work around https://jira.csiro.au/browse/WIRADA-635
            # lead_time can be a problem with xarray, so do not decode "times"
            x = xr.open_dataset(data, decode_times=False)

            # replace the time and station names coordinates values
            # TODO This is probably not a long term solution for round-tripping a read/write or vice and versa
            decod = times.CFDatetimeCoder(use_cftime=True)
            var = xr.as_variable(x.coords[TIME_DIMNAME])
            self.time_zone = var.attrs["time_standard"]
            time_coords = decod.decode(var, name=TIME_DIMNAME)
            time_coords.values = cftimes_to_pdtstamps(
                time_coords.values, self.time_zone,
            )
            stat_coords = x.coords[self.stations_dim_name]
            station_names = _byte_stations_to_str(x[station_name_varname].values)
            x = x.assign_coords(
                {TIME_DIMNAME: time_coords, self.stations_dim_name: station_names},
            )

            self.data = x
        else:
            self.data = data

    def get_all_series(self, variable_name="rain_obs", dimension_id=None):
        # Return a multivariate time series, where each column is the series for one of the identifiers (self, e.g. rainfall station identifiers):
        return self.data[variable_name]
        # stopifnot(variable_name %in% names(ncfile$var))
        # td = self.get_time_dim()
        # if dimension_id is None: dimension_id = self.get_stations_varname()
        # identifiers = self._get_values(dimension_id)
        # ncdims = self.get_variable_dim_names(variable_name)
        # could be e.g.: double q_obs[lead_time,station,ens_member,time] float
        # rain_obs[station,time] lead_time,station,ens_member,time reordered
        # according to the variable present dimensions:
        # tsstart = splice_named_var(c(1, 1, 1, 1), ncdims)
        # tscount = splice_named_var(c(1, length(identifiers), 1, length(td)), ncdims)
        # rawData = ncdf4::ncvar_get(ncfile, variable_name, start = tsstart, count = tscount,
        # collapse_degen = FALSE)
        # dim_names(rawData) = ncdims
        # # [station,time] to [time, station] for xts creation
        # # NOTE: why can this not be dimension_id instead of stations_dim_name?
        # tsData = reduce_dimensions(rawData,c(time_dim_name, stations_dim_name))
        # v = xts(x = tsData, order.by = td, tzone = tz(td))
        # colnames(v) = identifiers
        # return(v)

    def get_dim_names(self):
        # Gets the name of all dimensions in the data set
        return [x for x in self.data.dims.keys()]

    def get_ensemble_for_stations(
        self,
        variable_name="rain_sim",
        identifier: str = None,
        dimension_id="ens_member",
        start_time=None,
        lead_time_count=None,
    ):
        # Return a time series, representing a single ensemble member forecast for all stations over the lead time
        raise NotImplementedError

    def get_ensemble_forecasts(
        self,
        variable_name="rain_sim",
        identifier: str = None,
        dimension_id=None,
        start_time=None,
        lead_time_count=None,
    ) -> xr.DataArray:
        # Return a time series, ensemble of forecasts over the lead time
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        td = self.get_time_dim()
        if start_time is None:
            start_time = td[0]
        nEns = self.get_ensemble_size()
        index_id = self.index_for_identifier(identifier, dimension_id)
        check_index_found(index_id, identifier, dimension_id)
        if lead_time_count is None:
            lead_time_count = self.get_lead_time_count()
        indTime = self.index_for_time(start_time)
        # float rain_sim[lead_time,station,ens_member,time]
        ensData = self.data.get(variable_name)[
            indTime, :nEns, index_id, :lead_time_count,
        ]
        # ensData = self.data.get(variable_name), start = [1, index_id, 1, indTime],
        #     count = c(lead_time_count, 1, nEns, 1), collapse_degen = FALSE)
        # tu = self.get_lead_time_unit()
        # if tu == "days":
        #     timeAxis = start_time + pd.Timedelta(ncfile$dim$lead_time$vals)
        # } else {
        # timeAxis = start_time + lubridate::dhours(1) * ncfile$dim$lead_time$vals
        # }
        # out = xts(x = ensData[, 1, , 1], order.by = timeAxis, tzone = tz(start_time))
        return ensData

    def get_ensemble_forecasts_for_station(
        self, variable_name="rain_sim", identifier: str = None, dimension_id=None,
    ):
        # Return an array, representing all ensemble member forecasts for a single stations over all lead times
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        raise NotImplementedError

    def get_ensemble_series(
        self, variable_name="rain_ens", identifier: str = None, dimension_id=None,
    ):
        # Return an ensemble of point time series for a station identifier
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        raise NotImplementedError

    def get_ensemble_size(self):
        # Length of the ensemble size dimension
        return self.data.dims[self.ensemble_member_dim_name]

    def get_lead_time_count(self):
        # Length of the lead time dimension
        return self.data.dims[self.lead_time_dim_name]

    def get_single_series(
        self, variable_name="rain_obs", identifier: str = None, dimension_id=None,
    ):
        # Return a single point time series for a station identifier. Falls back on def get_all_series if the argument "identifier" is missing
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        return self.data[variable_name].sel({dimension_id: identifier})

    def get_station_count(self):
        # Length of the lead time dimension
        self.data.dims[self.stations_dim_name]

    def get_stations_varname(self):
        # Gets the name of the variable that has the station identifiers
        # TODO: station is integer normally in STF (Euargh)
        return station_id_varname

    def get_time_dim(self):
        # Gets the time dimension variable as a vector of date-time stamps
        return self.data.time.values  # but loosing attributes.

    def get_time_unit(self):
        # Gets the time units of a read time series, i.e. "hours since 2015-10-04 00:00:00 +1030". Returns the string "hours"
        return "dummy"

    def get_time_zone(self):
        # Gets the time zone to use for the read time series
        return "dummy"

    def get_utc_offset(self, as_string=True):
        # Gets the time zone to use for the read time series, i.e. "hours since 2015-10-04 00:00:00 +1030". Returns the string "+1030" or "-0845" if as_string is TRUE, or a lubridate Duration object if FALSE
        return None

    def _get_values(self, variable_name):
        # Gets (and cache in memory) all the values in a variable. Should be used only for dimension variables
        if variable_name not in conventional_varnames:
            raise Exception(
                variable_name
                + " cannot be directly retrieved. Must be in "
                + ", ".join(conventional_varnames),
            )
        return self.data[variable_name].values

    def get_variable_dim_names(self, variable_name):
        # Gets the names of the dimensions that define the geometry of a given variable
        return [x for x in self.data[[variable_name]].coords.keys()]

    def get_variable_names(self):
        # Gets the name of all variables in the data set
        return [x for x in self.data.variables.keys()]

    def index_for_identifier(self, identifier, dimension_id=None):
        # Gets the index at which an identifier is found in a dimension variable
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        identValues = self._get_values(dimension_id)
        if identifier is None:
            raise Exception("Identifier cannot be NA")
        else:
            return _first_where(identifier == identValues)

    def index_for_time(self, dateTime):
        # Gets the index at which a date-time is found in the main time axis of this data set
        return _first_where(self.data.time == dateTime)

    def put_ensemble_forecasts(
        self,
        x,
        variable_name="rain_sim",
        identifier: str = None,
        dimension_id=None,
        start_time=None,
    ):
        # Puts one or more ensemble forecast into a netCDF file
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        raise NotImplementedError

    def put_ensemble_forecasts_for_station(
        self,
        x,
        variable_name="rain_sim",
        identifier: str = None,
        dimension_id="ens_member",
        start_time=None,
    ):
        # Puts a single ensemble member forecasts for all stations into a netCDF file
        raise NotImplementedError

    def put_ensemble_series(
        self, x, variable_name="rain_ens", identifier: str = None, dimension_id=None,
    ):
        # Puts an ensemble of time series, e.g. replicate rainfall series
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        raise NotImplementedError

    def put_single_series(
        self,
        x,
        variable_name="rain_obs",
        identifier: str = None,
        dimension_id=None,
        start_time=None,
    ):
        # Puts a time series, or part thereof
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        raise NotImplementedError

    def put_values(self, x, variable_name):
        # Puts all the values in a variable. Should be used only for dimension variables
        raise NotImplementedError

    def set_time_zone(self, tzone_id):
        # Sets the time zone to use for the read time series
        raise NotImplementedError

    def summary(self):
        # Print a summary of this EFTS netCDF file
        raise NotImplementedError

    # See Also
    # See create_efts and open_efts for examples on how to read or write EFTS netCDF files using this dataset.


#' Creates a EftsDataSet for access to a netCDF EFTS data set
#'
#' Creates a EftsDataSet for access to a netCDF EFTS data set
#'
#' @param ncfile name of the netCDF file, or an object of class 'ncdf4'
#' @param writein if TRUE the data set is opened in write mode
#' @export
#' @import ncdf4
#' @examples
#' library(efts)
#' ext_data = system.file('extdata', package='efts')
#' ens_fcast_file = file.path(ext_data, 'Upper_Murray_sample_ensemble_rain_fcast.nc')
#' stopifnot(file.exists(ens_fcast_file))
#' snc = open_efts(ens_fcast_file)
#' (variable_names = snc$get_variable_names())
#' (stations_ids = snc$get_values('station_id'))
#' nEns = snc$get_ensemble_size()
#' nLead = snc$get_lead_time_count()
#' td = snc$get_time_dim()
#' stopifnot('rain_fcast_ens' %in% variable_names)
#'
#' ens_fcast_rainfall = snc$get_ensemble_forecasts('rain_fcast_ens',
#'   stations_ids[1], start_time=td[2])
#' names(ens_fcast_rainfall) = as.character(1:ncol(ens_fcast_rainfall))
#' plot(ens_fcast_rainfall, legend.loc='right')
#'
#' snc$close()
#'
#' @return A EftsDataSet object
#' @importFrom methods is
def open_efts(ncfile, writein=False):
    # raise NotImplemented("open_efts")
    # if isinstance(ncfile, str):
    #     nc = ncdf4::nc_open(ncfile, readunlim = FALSE, write = writein)
    # } else if (methods::is(ncfile, "ncdf4")) {
    #     nc = ncfile
    # }
    return EftsDataSet(ncfile)


#' Creates a EftsDataSet for write access to a netCDF EFTS data set
#'
#' Creates a EftsDataSet for write access to a netCDF EFTS data set
#'
#' @param fname file name to create to. The file must not exist already.
#' @param time_dim_info a list with the units and values defining the time dimension of the data set
#' @param data_var_definitions a data frame, acceptable by \code{\link{create_variable_definitions}}, or list of netCDF variable definitions, e.g.
#'       \code{list(rain_sim=list(name='rain_sim', longname='ECMWF Rainfall ensemble forecasts', units='mm', missval=-9999.0, precision='double', attributes=list(type=2, type_description='accumulated over the preceding interval')))}
#' @param stations_ids station identifiers, coercible to an integer vector (note: may change to be a more flexible character storage)
#' @param station_names optional; names of the stations
#' @param nc_attributes a named list of characters, attributes for the whole file,
#' including mandatory ones: title, institution, source, catchment, comment.
#' You may use \code{\link{create_global_attributes}} as a starting template.
#' @param lead_length length of the lead forecasting time series.
#' @param optional_vars a data frame defining optional netCDF variables. For a templated default see
#' \code{\link{default_optional_variable_definitions_v2_0}} and
#' \url{https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md#optional-variables}
#' @param lead_time_tstep string specifying the time step of the forecast lead length.
#' @param ensemble_length number of ensembles, i.e. number of forecasts for each point on the main time axis of the data set
#' @examples
#'
#' # NOTE
#' # The sample code below is purposely generic; to produce
#' # a data set conforming with the conventions devised for
#' # ensemble streamflow forecast you will need to
#' # follow the additional guidelines at
#' # https://github.com/jmp75/efts/blob/master/docs/netcdf_for_water_forecasting.md
#'
#' fname = tempfile()
#'
#' stations_ids = c(123,456)
#' nEns = 3
#' nLead = 4
#' nTimeSteps = 12
#'
#' timeAxisStart = ISOdate(year=2010, month=08, day=01, hour = 14, min = 0, sec = 0, tz = 'UTC')
#' time_dim_info = create_time_info(from=timeAxisStart,
#'   n=nTimeSteps, time_step = "hours since")
#'
#' # It is possible to define variables for three combinations of dimensions.
#' # dimensions '4' ==> [lead_time,station,ens_member,time]
#' # dimensions '3' ==> [station,ens_member,time]
#' # dimensions '2' ==> [station,time]
#'
#' variable_names = c('var1_fcast_ens','var2_fcast_ens', 'var1_obs',
#'   'var2_obs', 'var1_ens','var2_ens')
#'
#' va = create_var_attribute_definition(
#'   type = 2L,
#'   type_description = "accumulated over the preceding interval",
#'   dat_type = "der",
#'   dat_type_description = paste(rep(c("var1", "var2"), 3), "synthetic test data"),
#'   location_type = "Point")
#'
#'
#' (varDef = create_variable_definition_dataframe(
#'   variable_names=variable_names,
#'   long_names = paste(variable_names, 'synthetic data'),
#'   dimensions = c(4L,4L,2L,2L,3L,3L),
#'   var_attributes = va))
#'
#' glob_attr = create_global_attributes(
#'   title="data set title",
#'   institution="my org",
#'   catchment="Upper_Murray",
#'   source="A journal reference, URL",
#'   comment="example for vignette")
#'
#' (opt_metadatavars = default_optional_variable_definitions_v2_0())
#'
#' snc = create_efts(
#'   fname=fname,
#'   time_dim_info=time_dim_info,
#'   data_var_definitions=varDef,
#'   stations_ids=stations_ids,
#'   nc_attributes=glob_attr,
#'   optional_vars = opt_metadatavars,
#'   lead_length=nLead,
#'   ensemble_length=nEns,
#'   lead_time_tstep = "hours")
#'
#' # Following is code that was used to create unit tests for EFTS.
#' # This is kept in this example to provide sample on now to write data of various dimension.
#' td = snc$get_time_dim()
#' m = matrix(ncol=nEns, nrow=nLead)
#' for (rnum in 1:nLead) {
#'     for (cnum in 1:nEns) {
#'       m[rnum,cnum] = rnum*0.01 + cnum*0.1
#'   }
#' }
#' #      [,1] [,2] [,3]
#' # [1,] 0.11 0.21 0.31
#' # [2,] 0.12 0.22 0.32
#' # [3,] 0.13 0.23 0.33
#' # [4,] 0.14 0.24 0.34
#' for (i in 1:length(td)) {
#'   for (j in 1:length(stations_ids)) {
#'     station = stations_ids[j]
#'     var1Values = i + 0.1*j + m
#'     var2Values = 2*var1Values
#'     dtime = td[i]
#'     snc$put_ensemble_forecasts(var1Values, variable_name = variable_names[1],
#'       identifier = station, start_time = dtime)
#'     snc$put_ensemble_forecasts(var2Values, variable_name = variable_names[2],
#'       identifier = station, start_time = dtime)
#'   }
#' }
#'
#' timeSteps = 1:length(td)
#' for (j in 1:length(stations_ids)) {
#'   var3Values = timeSteps + 0.1*j
#'   var4Values = var3Values + 0.01*timeSteps + 0.001*j
#'
#'   station = stations_ids[j]
#'   snc$put_single_series(var3Values, variable_name = variable_names[3], identifier = station)
#'   snc$put_single_series(var4Values, variable_name = variable_names[4], identifier = station)
#' }
#'
#' for (j in 1:length(stations_ids)) {
#'
#'   var5Xts = matrix(rep(1:nEns, each=nTimeSteps) + timeSteps + 0.1*j, ncol=nEns)
#'
#'   # [time,ens_member] to [ens_member,time], as expected by put_ensemble_series
#'   var5Values = t(var5Xts)
#'   var6Values = 0.25 * var5Values
#'
#'   station = stations_ids[j]
#'   snc$put_ensemble_series(var5Values, variable_name = variable_names[5], identifier = station)
#'   snc$put_ensemble_series(var6Values, variable_name = variable_names[6], identifier = station)
#' }
#'
#' # We can get/put values for some metadata variables:
#' snc$get_values("x")
#' snc$put_values(c(1.1, 2.2), "x")
#' snc$put_values(letters[1:2], "station_name")
#'
#' # Direct get/set access to data variables, however, is prevented;
#' #  the following would thus cause an error:
#' # snc$get_values("var1_fcast_ens")
#'
#' snc$close()
#' # Cleaning up temp file:
#' if (file.exists(fname))
#'   file.remove(fname)
#'
#'
#'
#' @export
#' @import ncdf4
#' @importFrom utils packageDescription
#' @importFrom methods new
#' @return A EftsDataSet object
def create_efts(
    fname: str,
    time_dim_info: Dict,
    data_var_definitions: pd.DataFrame,
    stations_ids: List[int],
    station_names: List[str] = None,
    nc_attributes: Dict[str, str] = None,
    optional_vars=None,
    lead_length=48,
    ensemble_length=50,
    lead_time_tstep="hours",
):
    import xarray as xr

    if stations_ids is None:
        raise Exception(
            "You must provide station identifiers when creating a new EFTS netCDF data set",
        )

    if nc_attributes is None:
        raise Exception(
            "You must provide a suitable list for nc_attributes, including"
            + ", ".join(mandatory_global_attributes),
        )

    # check_global_attributes(nc_attributes)

    if os.path.exists(fname):
        raise FileExistsError("File already exists: " + fname)

    if isinstance(data_var_definitions, pd.DataFrame):
        data_var_definitions = create_variable_definitions(data_var_definitions)

    varDefs = create_efts_variables(
        data_var_definitions,
        time_dim_info,
        num_stations=len(stations_ids),
        lead_length=lead_length,
        ensemble_length=ensemble_length,
        optional_vars=optional_vars,
        lead_time_tstep=lead_time_tstep,
    )

    ## attributes for dimensions variables
    def add_dim_attribute(v, dimname, attr_key, attr_value):
        pass

    add_dim_attribute(varDefs, time_dim_name, "standard_name", time_dim_name)
    add_dim_attribute(varDefs, time_dim_name, "time_standard", "UTC")
    add_dim_attribute(varDefs, time_dim_name, "axis", "t")
    add_dim_attribute(varDefs, ensemble_member_dim_name, "standard_name", "ens_member")
    add_dim_attribute(varDefs, ensemble_member_dim_name, "axis", "u")
    add_dim_attribute(varDefs, lead_time_dim_name, "standard_name", "lead_time")
    add_dim_attribute(varDefs, lead_time_dim_name, "axis", "v")
    add_dim_attribute(varDefs, lat_varname, "axis", "y")
    add_dim_attribute(varDefs, lon_varname, "axis", "x")

    d = xr.Dataset(data_vars=varDefs, coords=None, attrs=None)

    ## Determine if there is real value in a tryCatch. What is the point if we cannot close/delete the file.
    # nc = tryCatch(
    #   createSchema(fname, varDefs, data_var_definitions, nc_attributes, optional_vars,
    #     stations_ids, lead_length, ensemble_length, station_names),
    #   error = function(e) {
    #     stop(paste("netCDF schema creation failed", e))
    #     None
    #   }, finally = function() {
    #   }
    # )
    # nc = createSchema(fname, varDefs, data_var_definitions, nc_attributes, optional_vars,
    #   stations_ids, lead_length, ensemble_length, station_names)

    return EftsDataSet(d)


# ########################################
# # Below are functions not exported
# ########################################

# infoList(theList) {
#   paste(paste(names(theList), theList, sep = ": "), collapse = ", ")
# }

# createSchema(fname, varDefs, data_var_definitions, nc_attributes, optional_vars,
#   stations_ids, lead_length, ensemble_length, station_names=NA) {

#   allVars = c(varDefs$datavars, varDefs$metadatavars)
#   nc = ncdf4::nc_create(fname, vars = allVars)

#   ## attributes for data variables
#   lapply(data_var_definitions, put_variable_attributes, nc)

#   ## attributes for dimensions variables
#   ncdf4::ncatt_put(nc, time_dim_name, "standard_name", time_dim_name)
#   ncdf4::ncatt_put(nc, time_dim_name, "time_standard", "UTC")
#   ncdf4::ncatt_put(nc, time_dim_name, "axis", "t")
#   ncdf4::ncatt_put(nc, ensemble_member_dim_name, "standard_name", "ens_member")
#   ncdf4::ncatt_put(nc, ensemble_member_dim_name, "axis", "u")
#   ncdf4::ncatt_put(nc, lead_time_dim_name, "standard_name", "lead_time")
#   ncdf4::ncatt_put(nc, lead_time_dim_name, "axis", "v")
#   ncdf4::ncatt_put(nc, lat_varname, "axis", "y")
#   ncdf4::ncatt_put(nc, lon_varname, "axis", "x")

#   ## attributes for optional metadata variables
#   if(!is.None(optional_vars))
#   {
#     var_names = rownames(optional_vars)
#     if("standard_name" %in% colnames(optional_vars)){
#       for (v in var_names) {
#         sn = optional_vars[v, "standard_name"]
#         if(!is.na(sn)) ncdf4::ncatt_put(nc, v, "standard_name", sn)
#       }
#     }
#     if(x_varname %in% var_names){
#       ncdf4::ncatt_put(nc, x_varname, "axis", "x")
#     }
#     if(y_varname %in% var_names){
#       ncdf4::ncatt_put(nc, y_varname, "axis", "y")
#     }
#   }

#   ## Add global attributes
#   ncdf4::ncatt_put(nc, 0, "STF_convention_version", 2)
#   ncdf4::ncatt_put(nc, 0, "STF_nc_spec", "https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md")
#   ncdf4::ncatt_put(nc, 0, "history",
#     paste(
#       as.character(lubridate::now(tzone="UTC")),
#       "UTC",
#       "file created with the R package efts", packageDescription("efts")$Version
#     ) %>% infoList)

#   if(!is.None(nc_attributes)) {
#     for (k in names(nc_attributes)) {
#       pad_global_attribute(nc, k, nc_attributes[k])
#     }
#   }

#   ## populate metadata variables
#   ncdf4::ncvar_put(nc, station_id_varname, stations_ids)
#   ncdf4::ncvar_put(nc, lead_time_dim_name, 1:lead_length)
#   ncdf4::ncvar_put(nc, ensemble_member_dim_name, 1:ensemble_length)
#   if (!is.None(station_names)) {
#     ncdf4::ncvar_put(nc, station_name_varname, station_names)
#   }
#   # One seems to need to close/reopen the newly created file, otherwise some
#   # ncvar_get operations will fail with a cryptic message.  I follow the
#   # advice in this and associated posts
#   # https://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2012/msg00270.html
#   ncdf4::nc_close(nc)
#   nc = ncdf4::nc_open(fname, write = TRUE, readunlim = FALSE)
#   return(nc)
# }
