# check_index_found(index_id, identifier, dimension_id) {
#   if (length(index_id) == 0)
#     stop(paste0("identifier '", identifier, "' not found in the dimension '",
#       dimension_id, "'"))
# }

# STATION_DIMNAME = "station"
# LEAD_TIME_DIMNAME = "lead_time"
# TIME_DIMNAME = "time"
# ENS_MEMBER_DIMNAME = "ens_member"
# STR_LEN_DIMNAME = "str_len"

# # int station_id[station]
# STATION_ID_VARNAME = "station_id"
# # char station_name[str_len,station]
# STATION_NAME_VARNAME = "station_name"
# # float lat[station]
# LAT_VARNAME = LAT_VARNAME
# # float lon[station]
# lon_varname = "lon"
# # float x[station]
# x_varname = "x"
# # float y[station]
# y_varname = "y"
# # float area[station]
# area_varname = "area"
# # float elevation[station]
# elevation_varname = "elevation"

# conventional_varnames = c(
#   STATION_DIMNAME ,
#   LEAD_TIME_DIMNAME ,
#   TIME_DIMNAME ,
#   ENS_MEMBER_DIMNAME ,
#   STR_LEN_DIMNAME ,
#   STATION_ID_VARNAME ,
#   STATION_NAME_VARNAME ,
#   LAT_VARNAME ,
#   lon_varname ,
#   x_varname ,
#   y_varname ,
#   area_varname ,
#   elevation_varname
# )

# mandatory_global_attributes = c("title", INSTITUTION_ATTR_KEY, SOURCE_ATTR_KEY, CATCHMENT_ATTR_KEY, COMMENT_ATTR_KEY)


# get_default_dim_order() {
#   return(c(LEAD_TIME_DIMNAME, STATION_DIMNAME, ENS_MEMBER_DIMNAME, TIME_DIMNAME))
# }

# splice_named_var(d, ncdims = character()) {
#   default_order = get_default_dim_order()
#   d = as.integer(d)
#   stopifnot(length(d) == 4)
#   stopifnot(is.vector(d))
#   # lead_time,station,ens_member,time
#   names(d) = default_order
#   if (length(ncdims) > 0) {
#     if (!all(ncdims %in% default_order)) {
#       stop(paste0("Invalid dimensions for a data variable: ", paste(ncdims,
#         collapse = ",")))
#     } else {
#       d = d[ncdims]
#       names(d) = ncdims
#     }
#   }
#   return(d)
# }


# dim_names(x) {
#   attr(x, 'dim_names')
# }

# "dim_names<-"(x, value) {
#   d = dim(x)
#   if(is.array(x)) {
#     if(length(d) != length(value)) stop("dim names is not equal to the number of dimensions of the array")
#     if(length(unique(value)) != length(d)) stop("specified dim names are not unique")
#   } else if (is.vector(x)){
#     stopifnot(length(value) == 1)
#   } else { stop('not an array nor a vector - cannot set dim_names')}
#   attr(x, 'dim_names') = value
#   return(x)
# }

# reduce_dimensions(x, subset_dim_names){
#   dimsize_input = dim(x)
#   dn = dim_names(x)
#   if(is.null(dn)) stop('the input array must have a valid dim_names attribute')
#   if(length(dn) != length(dimsize_input)) stop('the input array and its dim_names attribute are differing in length')

#   names(dimsize_input) = dn
#   if(missing(subset_dim_names) || is.na(subset_dim_names))
#     subset_dim_names = dn[dimsize_input > 1]

#   diffdim = setdiff(subset_dim_names, dn)
#   if (length(diffdim)>0) stop(paste0('Dimension names to slice but not found in array dim names: ', paste(diffdim, collpase=', ')))

#   dropped_dims = setdiff(dn,subset_dim_names)
#   if( any(dimsize_input[dropped_dims] > 1)) stop('Cannot drop non-degenerate when subsetting')

#   w = match(subset_dim_names,dn)
#   other = match(setdiff(dn, subset_dim_names),dn)

#   x_reordered = aperm(x, c(w, other))

#   reordered_dim_names = dn[c(w, other)]
#   reordered_dim_sizes = dim(x_reordered)

#   new_dim_sizes = reordered_dim_sizes[1:length(w)]
#   new_dim_names = reordered_dim_names[1:length(w)]

#   y = drop(x_reordered)
#   # We want however to maintain degenerate
#   # dimensions that have been explicitly asked for,
#   # and that would have been otherwise dropped
#   y = array(y, new_dim_sizes)

#   dim_names(y) = new_dim_names
#   return(y)
# }

#' @import magrittr
from typing import Any, Dict, Tuple

import xarray as xr

from efts_io.conventions import FILLVALUE_ATTR_KEY, UNITS_ATTR_KEY


def create_data_variable(data_var_def: Dict[str, Any], dimensions: Tuple[str, Tuple]) -> xr.Variable:
    import numpy as np
    import xarray as xr

    a = data_var_def
    #    (c("name", UNITS_ATTR_KEY) %in% names(a)) %>% all %>% stopifnot
    varname = a["name"]
    longname = a.get("longname", varname)
    precision = a.get("precision", "double")
    missval = a.get("missval", -9999)

    dimnames = [d[0] for d in dimensions]
    if not isinstance(dimnames[0], str):
        raise TypeError("Dimension names must be strings.")
    shape = tuple(len(d[1]) for d in dimensions)
    return xr.Variable(
        dims=dimnames,
        data=np.empty(shape, dtype=float),  # TODO: should this use precision?
        encoding={FILLVALUE_ATTR_KEY: missval},
        attrs={
            "longname": longname,
            UNITS_ATTR_KEY: a[UNITS_ATTR_KEY],
            "missval": missval,
            "precision": precision,
        },
    )

    # xr.Variable(dims=dimensions, data, attrs=None, encoding=None, fastpath=False)
    # vardef = ncdf4::ncvar_def(name = varname, units = a[UNITS_ATTR_KEY], dim = dimensions,
    # longname = ifelse("longname" %in% names(a), a["longname"], varname)
    # precision = ifelse("precision" %in% names(a), a["precision"], "double")
    # missval = ifelse("missval" %in% names(a), a["missval"]], -9999)
    # vardef = ncdf4::ncvar_def(name = varname, units = a[UNITS_ATTR_KEY], dim = dimensions,
    #     missval = missval, longname = longname, prec = precision)
