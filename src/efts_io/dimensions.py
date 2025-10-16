"""Functions to create and manipulate dimensions for netCDF files."""

from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Tuple, Union

# import netCDF4
import numpy as np
import pandas as pd
from cftime import DatetimeGregorian

from efts_io.conventions import (
    ENS_MEMBER_DIMNAME,
    FILLVALUE_ATTR_KEY,
    LEAD_TIME_DIMNAME,
    STATION_DIMNAME,
    STR_LEN_DIMNAME,
    TIME_DIMNAME,
    UNITS_ATTR_KEY,
)


def iso_date_time_str(t: Any) -> str:
    """Convert a date-time object to a string in ISO format, using space as separator."""
    return pd.Timestamp(t).isoformat(" ")


#' Check that a date-time is in the UTC time zone, and return the date time offset 'zero'
#'
#' Check that a date-time is in the UTC time zone, and return the date time offset 'zero'
#'
#' @param d an object coercible to a POSIXct
#' @export
#' @return a character, the time zone offset string '+0000'
#' @importFrom lubridate tz
#' @examples
#' start_time <- ISOdate(year=2010, month=08, day=01, hour = 12, min = 0, sec = 0, tz = 'UTC')
#' check_is_utc(d=start_time)
#'
def check_is_utc(d: Any) -> bool:
    """Check that a date-time is in the UTC time zone."""
    a = pd.Timestamp(d)
    if a.tz is None:
        return True  # ?
    z = a.tz
    from datetime import timezone

    return z == timezone.utc


#' Create a time axis unit known to work for netCDF
#'
#' Create a time axis unit known to work for netCDF
#'
#' @param d an object coercible to a POSIXct
#' @param time_step the character prefix to put before the date, in the netCDF time axis unit definition.
#' @param tzoffset an optional character, the time offset from UTC, e.g. '+1000' for 10 hours ahead of UTC.
#'   Can be missing, in which case it must be explicitly a UTC time.
#'   Note that the tzoffset completely supersedes the time zone if present.
#' @export
#' @return a character, the axis units to use for the netCDF 'time' dimension
#' @examples
#' start_time <- ISOdate(year=2010, month=08, day=01, hour = 12, min = 0, sec = 0, tz = 'UTC')
#' create_netcdf_time_axis(d=start_time)
#' start_time <- ISOdate(year=2015, month=10, day=04, hour = 01,
#'   min = 0, sec = 0, tz = 'Australia/Sydney')
#' create_netcdf_time_axis(d=start_time, tzoffset='+1000')
#'
def create_netcdf_time_axis(d: Any, time_step: str = "hours since", tzoffset: Optional[str] = None) -> str:
    """Create a time axis unit known to work for netCDF."""
    if tzoffset is None:
        if not check_is_utc(d):
            raise ValueError("date time must have UTC or GMT as time zone")
        tzoffset = "+0000"
    return " ".join([time_step, iso_date_time_str(as_naive_timestamp(d)), tzoffset])


def as_naive_timestamp(d: Union[datetime, pd.Timestamp]) -> pd.Timestamp:
    """Convert a date-time object to a naive timestamp."""
    return pd.Timestamp(
        year=d.year,
        month=d.month,
        day=d.day,
        hour=d.hour,
        minute=d.minute,
        second=d.second,
    )


#' Helper function to create the definition of the time dimension for use in a netCDF file
#'
#' Helper function to create the definition of the time dimension for use in a netCDF file. Defaults to create an hourly axis.
#'
#' @param from the start date of the time axis
#' @param n length of the time dimension
#' @param time_step unit prefix in the time dimension units
#' @param time_step_delta integer, length of time units between each steps
#' @param tzoffset an optional character, the time offset from UTC, e.g. '+1000' for 10 hours ahead of UTC. Can be missing, in which case 'from' must be explicitly a UTC time. Note that the tzoffset completely supersedes the time zone if present.
#' @import ncdf4
#' @export
#' @return A list with keys units and values
#' @seealso See
#'    \code{\link{create_efts}} for examples
#' @examples
#' timeAxisStart <- ISOdate(2015, 10, 4, 0, 0, 0, tz = "Australia/Canberra")
#' (time_dim_info <- create_time_info(from = timeAxisStart, n = 24L,
#'   time_step = "hours since", time_step_delta = 3L, tzoffset = "+1000"))
#'
#' # Note that the time zone information of thes sart date is NOT
#' # used by create_time_info; the tzoffset argument takes precedence
#' timeAxisStart <- ISOdate(2015, 10, 4, 0, 0, 0, tz = "Australia/Perth")
#' (time_dim_info <- create_time_info(from = timeAxisStart, n = 24L,
#'   time_step = "hours since", time_step_delta = 3L, tzoffset = "+1000"))
#'
def create_time_info(
    start: Any,
    n: int,
    time_step: str = "hours since",
    time_step_delta: int = 1,
    tzoffset: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper function to create the definition of the time dimension for use in a netCDF file."""
    return {
        UNITS_ATTR_KEY: create_netcdf_time_axis(
            d=start,
            time_step=time_step,
            tzoffset=tzoffset,
        ),
        "values": np.arange(0, n) * time_step_delta,
    }


# #' Retrieves the first date of the time dimension from a netCDF file
# #'
# #' Retrieves the first date of the time dimension from a netCDF file of daily data, given the units found in the netCDF attribute for the time dimension
# #'
# #' @param time_units The string description of the units of the time dimension e.g. 'days since 1980-01-01' or 'hours since 2010-08-01 13:00:00 +0000'
# #' @param time_zone the time zone to use for the returned value.
# #' @export
# #' @importFrom udunits2 ud.convert
# #' @importFrom stringr str_split
# #' @import lubridate
# #' @return A POSIXct object, origin of the time dimension as defined
# #' @examples
# #'
# #' x <- "hours since 2015-10-04 00:00:00 +1023"
# #' get_start_date(x)
# #' get_start_date(x,time_zone = 'UTC')
# #' get_start_date(x,time_zone = 'Australia/Perth')
# #' get_start_date(x,time_zone = 'Australia/Canberra')
# #'
# get_start_date(time_units, time_zone = "UTC") {

#   # temporary work around https://github.com/jmp75/efts/issues/3
#   udu <- stringr::str_split(time_units, pattern = ' +')[[1]]
#   s <- paste(udu[3], udu[4], sep='T')
#   dt <- ymd_hms(s)
#   if(is.na(dt)) stop(paste0('Could not parse date time out of string ', time_units))
#   return(dt)

#   # refDate <- lubridate::origin  #
#   # class(refDate) <- c("POSIXct", "POSIXt")  # workaround what I think is a lubridate bug (possibly now wolved);
#   # # try origin + days(1)  and its effect, visibly because of class ordering on origin.
#   # isDaily <- is_daily_time_step(time_units)
#   # refDateUnits <- paste(ifelse(isDaily, "days", "hours"), "since 1970-01-01 00:00:00 +0000")
#   # offsetSinceRef <- udunits2::ud.convert(0, time_units, refDateUnits)
#   # offsetFun <- get_time_step_function(time_units)
#   # startDateUtc <- refDate + offsetFun(offsetSinceRef)
#   # startDate <- lubridate::with_tz(startDateUtc, time_zone)
#   # return(startDate)
# }

# #' Retrieves the unit string of the time dimension from a netCDF file
# #'
# #' @export
# #' @param ncfile an object of class ncdf4
# #' @param TIME_DIMNAME The name of the time dimension, by default 'time' as per the CF conventions.
# #' @return a character
# get_time_units(ncfile, TIME_DIMNAME = "time") {
#   return(ncdf4::ncatt_get(ncfile, TIME_DIMNAME, UNITS_ATTR_KEY)$value)
# }

# #' Retrieves the time dimension from a netCDF file
# #'
# #' @export
# #' @param ncfile an object of class ncdf4
# #' @param TIME_DIMNAME The name of the time dimension, by default 'time' as per the CF conventions.
# #' @param time_zone the time zone to use for the returned value.
# #' @return A vector of Dates
# get_time_dimension(ncfile, TIME_DIMNAME = "time", time_zone = "UTC") {
#   time_units <- get_time_units(ncfile, TIME_DIMNAME)
#   timeValues <- ncdf4::ncvar_get(ncfile, TIME_DIMNAME)
#   startDate <- get_start_date(time_units, time_zone = time_zone)
#   offsetFun <- get_time_step_function(time_units)
#   startDate + offsetFun(timeValues)
# }

# #' @importFrom stringr str_sub
# offset_as_duration(delta) {
#   h <- stringr::str_sub(delta, 1L, 2L)  # 10
#   m <- stringr::str_sub(delta, 3L, 4L)  # 30
#   return((lubridate::dhours(as.integer(h)) + lubridate::dminutes(as.integer(m))))
# }

# #' @importFrom stringr str_sub
# offset_as_difftime(delta) {
#   h <- stringr::str_sub(delta, 1L, 2L)  # 10
#   m <- stringr::str_sub(delta, 3L, 4L)  # 30
#   b <- lubridate::origin + lubridate::dhours(as.integer(h)) + lubridate::dminutes(as.integer(m))
#   b - lubridate::origin
# }

# #' Finds the UTC offset in a date-time string
# #'
# #' Finds the UTC offset in a date-time or time axis specification string
# #'  such as 'hours since 2015-10-04 00:00:00 +1030'
# #'
# #' @param time_units the string to process
# #' @param as_string a boolean. If true, return the time offset as a character, otherwise return a difftime object.
# #' @return the time offset as a character, or as a difftime object.
# #' @export
# #' @examples
# #'
# #' x <- "hours since 2015-10-04 00:00:00 +1023"
# #' find_utc_offset(x)
# #' find_utc_offset(x, FALSE)
# #' x <- "hours since 2015-10-04 00:00:00 -0837"
# #' find_utc_offset(x)
# #' find_utc_offset(x, FALSE)
# #' x <- "hours since 2015-10-04 00:00:00"
# #' find_utc_offset(x)
# #' find_utc_offset(x, FALSE)
# #'
# find_utc_offset(time_units, as_string = TRUE) {
#   # TODO: there may be a smarter way using udunits to determine the offset,
#   # but not trivial either.
#   x <- stringr::str_split(time_units, "\\+")[[1]]
#   # [1] 'hours since 2015-10-04 00:00:00 ' '1030' the offset would have been
#   # with a positive sign: +1030
#   if (length(x) > 1) {
#     delta <- last(x)  # 1030
#     if (as_string) {
#       return(paste0("+", delta))
#     } else {
#       return(+offset_as_difftime(delta))
#     }
#   }
#   x <- stringr::str_split(time_units, "[\\-]")[[1]]
#   # [1] 'hours since 2015' '10' '04 00:00:00 ' '1030' the offset would have
#   # been with a negative sign: -1030
#   if (length(x) == 4) {
#     delta <- last(x)  # 1030
#     if (as_string) {
#       return(paste0("-", delta))
#     } else {
#       return(-offset_as_difftime(delta))
#     }
#   } else {
#     # length(x) < 4 : no offset detected
#     if (as_string) {
#       return("")
#     } else {
#       return(lubridate::origin - lubridate::origin)
#     }
#   }
# }


# ########################################
# # Below are functions not exported
# ########################################

# is_daily_time_step(time_units) {
#   isDaily <- charmatch("days since", time_units)
#   isDaily <- ifelse(is.na(isDaily), FALSE, isDaily == 1)
#   isHourly <- charmatch("hours since", time_units)
#   isHourly <- ifelse(is.na(isHourly), FALSE, isHourly == 1)
#   if (!(isDaily | isHourly))
#     stop(paste("Could not detect if hourly or daily - unit not supported:",
#       time_units))
#   isDaily
# }

# #' Detect the unit of the time step in the time axis unit
# #'
# #' @param time_units The string description of the units of the time dimension e.g. 'days since 1980-01-01' or 'hours since 2010-08-01 13:00:00 +0000'
# #' @import lubridate
# #' @return A duration function from lubridate
# get_time_step_function(time_units) {
#   isDaily <- is_daily_time_step(time_units)
#   offsetFun <- ifelse(isDaily, lubridate::ddays, lubridate::dhours)
#   return(offsetFun)
# }


def _cftime_to_pdtstamp(t: pd.Timestamp, tz_str: Optional[str]) -> pd.Timestamp:
    return pd.Timestamp(t.isoformat(), tz=tz_str)


_as_tstamps = np.vectorize(_cftime_to_pdtstamp)


def cftimes_to_pdtstamps(
    cftimes: Iterable[DatetimeGregorian],
    tz_str: Optional[str] = None,
) -> np.ndarray[pd.Timestamp, pd.Timestamp]:
    """Convert one or more Climate and Forecast (CF) times to timestamps."""
    return _as_tstamps(cftimes, tz_str)


def create_timestamps(
    time_dim_info: Dict[str, Any],
    tz_str: Optional[str] = None,
) -> np.ndarray[pd.Timestamp, pd.Timestamp]:
    """Create time axis timestamps given the time dimension information."""
    import xarray as xr

    axis_units = time_dim_info[UNITS_ATTR_KEY]
    axis_values = time_dim_info["values"]
    var = xr.Variable(
        dims=[TIME_DIMNAME],
        data=axis_values,
        encoding={FILLVALUE_ATTR_KEY: None},
        attrs={
            UNITS_ATTR_KEY: axis_units,
        },
    )
    from xarray.coding import times

    decod = times.CFDatetimeCoder(use_cftime=True)
    time_coords = decod.decode(var, name=TIME_DIMNAME)
    return cftimes_to_pdtstamps(time_coords.values, tz_str=tz_str)


#' Creates dimensions for a netCDF EFTS data set
#'
#' Creates dimensions for a netCDF EFTS data set. Note that end users are unlikely to need to use this function directly, hence this is not exported
#'
#' @param time_dim_info a list with the units and values defining the time dimension of the data set
#' @param str_len maximum length of the character for the station identifiers.
#' @param lead_length length of the lead time.
#' @param ensemble_length number of ensembles, i.e. number of forecasts for each point on the main time axis of the data set
#' @param num_stations number of stations
#' @import ncdf4
#' @return A list of ncdf4 dimensions
#' @seealso See
#'    \code{\link{create_efts}} for examples
def _create_nc_dims(
    time_dim_info: Dict[str, Any],
    str_len: int = 30,
    lead_length: int = 1,
    ensemble_length: int = 1,
    num_stations: int = 1,
) -> Dict[str, Tuple[str, np.ndarray, Dict[str, str]]]:
    """Creates dimensions for a netCDF EFTS data set."""
    time_dim = (
        TIME_DIMNAME,
        time_dim_info["values"],
        {UNITS_ATTR_KEY: time_dim_info[UNITS_ATTR_KEY], "longname": "time"},
    )
    # time_dim = ncdf4::ncdim_def(TIME_DIMNAME, units = time_dim_info$units, vals = time_dim_info$values,
    #     unlim = T, create_dimvar = TRUE, longname = "time")
    station_dim = (
        STATION_DIMNAME,
        np.arange(1, num_stations + 1),
        {UNITS_ATTR_KEY: "", "longname": STATION_DIMNAME},
    )
    str_dim = (
        STR_LEN_DIMNAME,
        np.arange(1, str_len + 1),
        {UNITS_ATTR_KEY: "", "longname": "string length"},
    )
    lead_time_dim = (
        LEAD_TIME_DIMNAME,
        np.arange(1, lead_length + 1),
        {UNITS_ATTR_KEY: "", "longname": "lead time"},
    )  # TODO: check whether  time_dim_info['units'] is alwaus suitable.
    ensemble_dim = (
        ENS_MEMBER_DIMNAME,
        np.arange(1, ensemble_length + 1),
        {UNITS_ATTR_KEY: "", "longname": "ensemble"},
    )
    return {
        "time_dim": time_dim,
        "lead_time_dim": lead_time_dim,
        "station_dim": station_dim,
        "str_dim": str_dim,
        "ensemble_dim": ensemble_dim,
    }
