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
