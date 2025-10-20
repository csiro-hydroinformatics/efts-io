"""A thin wrapper around xarray for reading and writing Ensemble Forecast Time Series (EFTS) data sets."""

import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

# import netCDF4
import numpy as np
import pandas as pd
import xarray as xr

from efts_io._ncdf_stf2 import StfDataType, StfVariable
from efts_io.conventions import (
    AREA_VARNAME,
    AXIS_ATTR_KEY,
    CATCHMENT_ATTR_KEY,
    COMMENT_ATTR_KEY,
    ENS_MEMBER_DIMNAME,
    HISTORY_ATTR_KEY,
    INSTITUTION_ATTR_KEY,
    LAT_VARNAME,
    LEAD_TIME_DIMNAME,
    LON_VARNAME,
    LONG_NAME_ATTR_KEY,
    REALISATION_DIMNAME,
    SOURCE_ATTR_KEY,
    STANDARD_NAME_ATTR_KEY,
    STATION_DIMNAME,
    STATION_ID_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    STF_2_0_URL,
    STF_CONVENTION_VERSION_ATTR_KEY,
    STF_NC_SPEC_ATTR_KEY,
    TIME_DIMNAME,
    TIME_STANDARD_ATTR_KEY,
    TITLE_ATTR_KEY,
    UNITS_ATTR_KEY,
    ConvertibleToTimestamp,
    check_index_found,
)
from efts_io.dimensions import cftimes_to_pdtstamps
from efts_io.variables import create_efts_variables


def byte_to_string(x: Union[int, bytes]) -> str:
    """Convert a byte to a string."""
    if isinstance(x, int):
        if x > 255 or x < 0:  # noqa: PLR2004
            raise ValueError("Integer value to bytes: must be in range [0-255]")
        x = x.to_bytes(1, "little")
    if not isinstance(x, bytes):
        raise TypeError(f"Cannot cast type {type(x)} to bytes")
    return str(x, encoding="UTF-8")


def byte_array_to_string(x: np.ndarray) -> str:
    """Convert a byte array to a string."""
    s = "".join([byte_to_string(s) for s in x])
    return s.strip()


def byte_stations_to_str(byte_names: np.ndarray) -> np.ndarray:
    """Convert byte array of station names to string array."""
    return np.array([byte_array_to_string(x) for x in byte_names])


def _first_where(condition: np.ndarray) -> int:
    """Return the first index where the condition is true."""
    x = np.where(condition)[0]
    if len(x) < 1:
        raise ValueError("first_where: Invalid condition, no element is true")
    return x[0]


def load_from_stf2_file(file_path: str, time_zone_timestamps: bool) -> xr.Dataset:  # noqa: FBT001
    """Load data from an STF 2.0 netcdf file to an xarray representation.

    Args:
        file_path (str): file path
        time_zone_timestamps (bool): should we try to recognise the time zone and include it in each xarray time stamp?

    Returns:
        _type_: xarray Dataset
    """
    from xarray.coding import times

    # work around https://jira.csiro.au/browse/WIRADA-635
    # lead_time can be a problem with xarray, so do not decode "times"
    x = xr.open_dataset(file_path, decode_times=False)

    # replace the time and station names coordinates values
    # TODO This is probably not a long term solution for round-tripping a read/write or vice and versa
    decod = times.CFDatetimeCoder(use_cftime=True)
    var = xr.as_variable(x.coords[TIME_DIMNAME])
    time_zone = var.attrs[TIME_STANDARD_ATTR_KEY]
    time_coords = decod.decode(var, name=TIME_DIMNAME)
    tz = time_zone if time_zone_timestamps else None
    time_coords.values = cftimes_to_pdtstamps(
        time_coords.values,
        tz_str=tz,
    )
    # stat_coords = x.coords[self.STATION_DIMNAME]
    # see the use of astype later on in variable transfer, following line not needed.
    # station_names = byte_stations_to_str(x[STATION_NAME_VARNAME].values).astype(np.str_)
    station_ids_strings = x[STATION_ID_VARNAME].values.astype(np.str_)
    # x = x.assign_coords(
    #     {TIME_DIMNAME: time_coords, self.STATION_DIMNAME: station_names},
    # )

    # Create a new dataset with the desired structure
    new_dataset = xr.Dataset(
        coords={
            REALISATION_DIMNAME: (REALISATION_DIMNAME, x[ENS_MEMBER_DIMNAME].values),
            LEAD_TIME_DIMNAME: (LEAD_TIME_DIMNAME, x[LEAD_TIME_DIMNAME].values),
            STATION_ID_DIMNAME: (STATION_ID_DIMNAME, station_ids_strings),
            TIME_DIMNAME: (TIME_DIMNAME, time_coords),
        },
        attrs=x.attrs,
    )
    # Copy data variables from the renamed dataset
    for var_name in x.data_vars:
        if var_name not in (STATION_ID_VARNAME, STATION_NAME_VARNAME):
            # Get the variable from the original dataset
            orig_var = x[var_name]
            # Determine the dimensions for the new variable
            new_dims = []
            for dim in orig_var.dims:
                if dim == ENS_MEMBER_DIMNAME:
                    new_dims.append(REALISATION_DIMNAME)
                elif dim == STATION_DIMNAME:
                    new_dims.append(STATION_ID_DIMNAME)
                else:
                    new_dims.append(dim)
            # Create a new DataArray with the correct dimensions
            new_dataset[var_name] = xr.DataArray(
                data=orig_var.values,
                dims=new_dims,
                coords={dim: new_dataset[dim] for dim in new_dims if dim in new_dataset.coords},
                attrs=orig_var.attrs,
            )
    # Handle station names separately
    station_names_var = x[STATION_NAME_VARNAME]
    new_dataset[STATION_NAME_VARNAME] = xr.DataArray(
        data=station_names_var.values.astype(np.str_),
        dims=[STATION_ID_DIMNAME],
        coords={STATION_ID_DIMNAME: new_dataset[STATION_ID_DIMNAME]},
        attrs=station_names_var.attrs,
    )
    return new_dataset


class EftsDataSet:
    """Convenience class for access to a Ensemble Forecast Time Series in netCDF file."""

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

    def __init__(self, data: Union[str, xr.Dataset]) -> None:
        """Create a new EftsDataSet object."""
        self.time_dim = None
        self.time_zone = "UTC"
        self.time_zone_timestamps = True  # Not sure about https://github.com/csiro-hydroinformatics/efts-io/issues/3
        self.STATION_DIMNAME = STATION_DIMNAME
        self.stations_varname = STATION_ID_VARNAME
        self.LEAD_TIME_DIMNAME = LEAD_TIME_DIMNAME
        self.ENS_MEMBER_DIMNAME = ENS_MEMBER_DIMNAME
        # self.identifiers_dimensions: list = []
        self.data: xr.Dataset
        if isinstance(data, str):
            new_dataset = load_from_stf2_file(data, self.time_zone_timestamps)
            self.data = new_dataset
        else:
            self.data = data

        self.stf2_int_datatype = "i4"  # default integer type for STF2 saving

    @property
    def title(self) -> str:
        """Get or set the title attribute of the dataset."""
        return self.data.attrs.get(TITLE_ATTR_KEY, "")

    @title.setter
    def title(self, value: str) -> None:
        """Get or set the title attribute of the dataset."""
        self.data.attrs[TITLE_ATTR_KEY] = value

    @property
    def institution(self) -> str:
        """Get or set the institution attribute of the dataset."""
        return self.data.attrs.get(INSTITUTION_ATTR_KEY, "")

    @institution.setter
    def institution(self, value: str) -> None:
        """Get or set the institution attribute of the dataset."""
        self.data.attrs[INSTITUTION_ATTR_KEY] = value

    @property
    def source(self) -> str:
        """Get or set the source attribute of the dataset."""
        return self.data.attrs.get(SOURCE_ATTR_KEY, "")

    @source.setter
    def source(self, value: str) -> None:
        """Get or set the source attribute of the dataset."""
        self.data.attrs[SOURCE_ATTR_KEY] = value

    @property
    def catchment(self) -> str:
        """Get or set the catchment attribute of the dataset."""
        return self.data.attrs.get(CATCHMENT_ATTR_KEY, "")

    @catchment.setter
    def catchment(self, value: str) -> None:
        """Get or set the catchment attribute of the dataset."""
        self.data.attrs[CATCHMENT_ATTR_KEY] = value

    @property
    def stf_convention_version(self) -> float:
        """Get or set the STF_convention_version attribute of the dataset."""
        return self.data.attrs.get(STF_CONVENTION_VERSION_ATTR_KEY, "")

    @stf_convention_version.setter
    def stf_convention_version(self, value: float) -> None:
        """Get or set the STF_convention_version attribute of the dataset."""
        self.data.attrs[STF_CONVENTION_VERSION_ATTR_KEY] = value

    @property
    def stf_nc_spec(self) -> str:
        """Get or set the STF_nc_spec attribute of the dataset."""
        return self.data.attrs.get(STF_NC_SPEC_ATTR_KEY, "")

    @stf_nc_spec.setter
    def stf_nc_spec(self, value: str) -> None:
        """Get or set the STF_nc_spec attribute of the dataset."""
        self.data.attrs[STF_NC_SPEC_ATTR_KEY] = value

    @property
    def comment(self) -> str:
        """Get or set the comment attribute of the dataset."""
        return self.data.attrs.get(COMMENT_ATTR_KEY, "")

    @comment.setter
    def comment(self, value: str) -> None:
        """Get or set the comment attribute of the dataset."""
        self.data.attrs[COMMENT_ATTR_KEY] = value

    @property
    def history(self) -> str:
        """Gets/sets the history attribute of the dataset."""
        return self.data.attrs.get(HISTORY_ATTR_KEY, "")

    @history.setter
    def history(self, value: str) -> None:
        """Gets/sets the history attribute of the dataset."""
        self.data.attrs[HISTORY_ATTR_KEY] = value

    def append_history(self, message: str, timestamp: Optional[datetime] = None) -> None:
        """Append a new entry to the `history` attribute with a timestamp.

        message: The message to append.
        timestamp: If not provided, the current UTC time is used.
        """
        if timestamp is None:
            timestamp = datetime.now(datetime.timezone.utc).isoformat()

        current_history = self.data.attrs.get(HISTORY_ATTR_KEY, "")
        if current_history:
            self.data.attrs[HISTORY_ATTR_KEY] = f"{current_history}\n{timestamp} - {message}"
        else:
            self.data.attrs[HISTORY_ATTR_KEY] = f"{timestamp} - {message}"

    def to_netcdf(self, path: str, version: Optional[str] = "2.0") -> None:
        """Write the data set to a netCDF file."""
        if version is None:
            self.data.to_netcdf(path)
        elif version == "2.0":
            self.save_to_stf2(path)
        else:
            raise ValueError("Only version 2.0 is supported for now")

    def set_mandatory_global_attributes(
        self,
        title: str = "not provided",
        institution: str = "not provided",
        catchment: str = "not provided",
        source: str = "not provided",
        comment: str = "not provided",
        history: str = "not provided",
        append_history: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Sets mandatory global attributes for an EFTS dataset."""
        self.title = title
        self.institution = institution
        self.catchment = catchment
        self.source = source
        self.comment = comment
        if append_history:
            self.append_history(history)
        else:
            self.history = history
        self.stf_convention_version = "2.0"
        self.stf_nc_spec = STF_2_0_URL

    def writeable_to_stf2(self) -> bool:
        """Check if the dataset can be written to a netCDF file compliant with STF 2.0 specification.

        This method checks if the underlying xarray dataset or dataarray has the required dimensions and global attributes as specified by the STF 2.0 convention.

        Returns:
            bool: True if the dataset can be written to a STF 2.0 compliant netCDF file, False otherwise.
        """
        from efts_io.conventions import exportable_to_stf2

        return exportable_to_stf2(self.data)

    @property
    def stf2_int_datatype(self) -> str:
        """The type of integer to save to in the STF 2.x netcdf convention: 'i4' or 'i8'."""
        return self._stf2_int_datatype

    @stf2_int_datatype.setter
    def stf2_int_datatype(self, value: str) -> None:
        """The type of integer to save to in the STF 2.x netcdf convention: 'i4' or 'i8'."""
        if value not in ("i4", "i8"):
            raise ValueError("stf2_int_datatype must be either 'i4' or 'i8'")
        self._stf2_int_datatype = value

    def save_to_stf2(
        self,
        path: str,
        variable_name: Optional[str] = None,
        var_type: StfVariable = StfVariable.STREAMFLOW,
        data_type: StfDataType = StfDataType.OBSERVED,
        ens: bool = False,  # noqa: FBT001, FBT002
        timestep: str = "days",
        data_qual: Optional[xr.DataArray] = None,
    ) -> None:
        """Save to file."""
        from efts_io._ncdf_stf2 import write_nc_stf2

        if isinstance(self.data, xr.Dataset):
            if variable_name is None:
                raise ValueError("Inner data is a DataSet, so an explicit variable name must be explicitely specified.")
            d = self.data[variable_name]
        # elif isinstance(self.data, xr.DataArray):
        #    d = self.data
        else:
            raise TypeError(f"Unsupported data type {type(self.data)}")
        write_nc_stf2(
            out_nc_file=path,  # : str,
            dataset=self.data,
            data=d,  # : xr.DataArray,
            var_type=var_type,  # : int = 1,
            data_type=data_type,  # : int = 3,
            stf_nc_vers=2,  # : int = 2,
            ens=ens,  # : bool = False,
            timestep=timestep,  # :str="days",
            data_qual=data_qual,  # : Optional[xr.DataArray] = None,
            overwrite=True,  # :bool=True,
            # loc_info=loc_info, # : Optional[Dict[str, Any]] = None,
            intdata_type=self.stf2_int_datatype,
        )

    def create_data_variables(self, data_var_def: Dict[str, Dict[str, Any]]) -> None:
        """Create data variables in the data set.

        var_defs_dict["variable_1"].keys()
        dict_keys(['name', 'longname', 'units', 'dim_type', 'missval', 'precision', 'attributes'])
        """
        ens_fcast_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "4"]
        ens_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "3"]
        point_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "2"]

        four_dims_names = (LEAD_TIME_DIMNAME, STATION_ID_DIMNAME, REALISATION_DIMNAME, TIME_DIMNAME)
        three_dims_names = (STATION_ID_DIMNAME, REALISATION_DIMNAME, TIME_DIMNAME)
        two_dims_names = (STATION_ID_DIMNAME, TIME_DIMNAME)

        four_dims_shape = tuple(self.data.sizes[dimname] for dimname in four_dims_names)
        three_dims_shape = tuple(self.data.sizes[dimname] for dimname in three_dims_names)
        two_dims_shape = tuple(self.data.sizes[dimname] for dimname in two_dims_names)
        for vardefs, dims_shape, dims_names in [
            (ens_fcast_data_var_def, four_dims_shape, four_dims_names),
            (ens_data_var_def, three_dims_shape, three_dims_names),
            (point_data_var_def, two_dims_shape, two_dims_names),
        ]:
            for x in vardefs:
                varname = x["name"]
                self.data[varname] = xr.DataArray(
                    name=varname,
                    data=nan_full(dims_shape),
                    coords=self.data.coords,
                    dims=dims_names,
                    attrs={
                        "longname": x["longname"],
                        UNITS_ATTR_KEY: x[UNITS_ATTR_KEY],
                        "missval": x["missval"],
                        "precision": x["precision"],
                        **x["attributes"],
                    },
                )

    def get_all_series(
        self,
        variable_name: str = "rain_obs",
        dimension_id: Optional[str] = None,  # noqa: ARG002
    ) -> xr.DataArray:
        """Return a multivariate time series, where each column is the series for one of the identifiers."""
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
        # # NOTE: why can this not be dimension_id instead of STATION_DIMNAME?
        # tsData = reduce_dimensions(rawData,c(TIME_DIMNAME, STATION_DIMNAME))
        # v = xts(x = tsData, order.by = td, tzone = tz(td))
        # colnames(v) = identifiers
        # return(v)

    def get_dim_names(self) -> List[str]:
        """Gets the name of all dimensions in the data set."""
        return [x for x in self.data.sizes.keys()]  # noqa: C416, SIM118
        # Note: self._dim_size will return a list of str in the future
        # return [x for x in self._dim_size.keys()]

    def get_ensemble_for_stations(
        self,
        variable_name: str = "rain_sim",
        identifier: Optional[str] = None,
        dimension_id: str = ENS_MEMBER_DIMNAME,
        start_time: pd.Timestamp = None,
        lead_time_count: Optional[int] = None,
    ) -> xr.DataArray:
        """Not yet implemented."""
        # Return a time series, representing a single ensemble member forecast for all stations over the lead time
        raise NotImplementedError

    def get_ensemble_forecasts(
        self,
        variable_name: str = "rain_sim",
        identifier: Optional[str] = None,
        dimension_id: Optional[str] = None,
        start_time: Optional[pd.Timestamp] = None,
        lead_time_count: Optional[int] = None,
    ) -> xr.DataArray:
        """Gets an ensemble forecast for a variable."""
        # Return a time series, ensemble of forecasts over the lead time
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        td = self.get_time_dim()
        if start_time is None:
            start_time = td[0]
        n_ens = self.get_ensemble_size()
        raise NotImplementedError(
            "get_ensemble_forecasts: not yet implemented",
        )
        index_id = self.index_for_identifier(identifier, dimension_id)
        check_index_found(index_id, identifier, dimension_id)
        if lead_time_count is None:
            lead_time_count = self.get_lead_time_count()
        indx_time = self.index_for_time(start_time)
        # float rain_sim[lead_time,station,ens_member,time]
        ens_data = self.data.get(variable_name)[
            indx_time,
            :n_ens,
            index_id,
            :lead_time_count,
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
        return ens_data  # noqa: RET504

    # def get_ensemble_forecasts_for_station(
    #     self,
    #     variable_name: str = "rain_sim",
    #     identifier: Optional[str] = None,
    #     dimension_id: Optional[str] = None,
    # ):
    #     """Return an array, representing all ensemble member forecasts for a single stations over all lead times."""
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     raise NotImplementedError

    # def get_ensemble_series(
    #     self,
    #     variable_name: str = "rain_ens",
    #     identifier: Optional[str] = None,
    #     dimension_id: Optional[str] = None,
    # ):
    #     """Return an ensemble of point time series for a station identifier."""
    #     # Return an ensemble of point time series for a station identifier
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     raise NotImplementedError

    def _dim_size(self, dimname: str) -> int:
        return self.data.sizes[dimname]

    def get_ensemble_size(self) -> int:
        """Return the length of the ensemble size dimension."""
        return self._dim_size(self.ENS_MEMBER_DIMNAME)

    def get_lead_time_count(self) -> int:
        """Length of the lead time dimension."""
        return self._dim_size(self.LEAD_TIME_DIMNAME)

    def get_lead_time_values(self) -> np.ndarray:
        """Return the values of the lead time dimension."""
        return self.data[self.LEAD_TIME_DIMNAME].values

    def put_lead_time_values(self, values: Iterable[float]) -> None:
        """Set the values of the lead time dimension."""
        self.data[self.LEAD_TIME_DIMNAME].values = np.array(values)

    def get_single_series(
        self,
        variable_name: str = "rain_obs",
        identifier: Optional[str] = None,
        dimension_id: Optional[str] = None,
    ) -> xr.DataArray:
        """Return a single point time series for a station identifier."""
        # Return a single point time series for a station identifier. Falls back on def get_all_series if the argument "identifier" is missing
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        return self.data[variable_name].sel({dimension_id: identifier})

    def get_station_count(self) -> int:
        """Return the number of stations in the data set."""
        self._dim_size(self.STATION_DIMNAME)

    def get_stations_varname(self) -> str:
        """Return the name of the variable that has the station identifiers."""
        # Gets the name of the variable that has the station identifiers
        # TODO: station is integer normally in STF (Euargh)
        return STATION_ID_VARNAME

    def get_time_dim(self) -> np.ndarray:
        """Return the time dimension variable as a vector of date-time stamps."""
        # Gets the time dimension variable as a vector of date-time stamps
        return self.data.time.values  # but loosing attributes.

    # def get_time_unit(self) -> str:
    #     """Return the time units of a read time series."""
    #     # Gets the time units of a read time series, i.e. "hours since 2015-10-04 00:00:00 +1030". Returns the string "hours"
    #     return "dummy"

    # def get_time_zone(self) -> str:
    #     # Gets the time zone to use for the read time series
    #     return "dummy"

    # def get_utc_offset(self, as_string: bool = True):
    #     # Gets the time zone to use for the read time series, i.e. "hours since 2015-10-04 00:00:00 +1030". Returns the string "+1030" or "-0845" if as_string is TRUE, or a lubridate Duration object if FALSE
    #     return None

    # def _get_values(self, variable_name: str):
    #     # Gets (and cache in memory) all the values in a variable. Should be used only for dimension variables
    #     from efts_io.conventions import conventional_varnames

    #     if variable_name not in conventional_varnames:
    #         raise ValueError(
    #             variable_name + " cannot be directly retrieved. Must be in " + ", ".join(conventional_varnames),
    #         )
    #     return self.data[variable_name].values

    # def get_variable_dim_names(self, variable_name):
    #     # Gets the names of the dimensions that define the geometry of a given variable
    #     return [x for x in self.data[[variable_name]].coords.keys()]

    # def get_variable_names(self):
    #     # Gets the name of all variables in the data set
    #     return [x for x in self.data.variables.keys()]

    # def index_for_identifier(self, identifier, dimension_id=None):
    #     # Gets the index at which an identifier is found in a dimension variable
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     identValues = self._get_values(dimension_id)
    #     if identifier is None:
    #         raise Exception("Identifier cannot be NA")
    #     return _first_where(identifier == identValues)

    # def index_for_time(self, dateTime):
    #     # Gets the index at which a date-time is found in the main time axis of this data set
    #     return _first_where(self.data.time == dateTime)

    # def put_ensemble_forecasts(
    #     self,
    #     x,
    #     variable_name="rain_sim",
    #     identifier: str = None,
    #     dimension_id=None,
    #     start_time=None,
    # ):
    #     # Puts one or more ensemble forecast into a netCDF file
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     raise NotImplementedError

    # def put_ensemble_forecasts_for_station(
    #     self,
    #     x,
    #     variable_name="rain_sim",
    #     identifier: str = None,
    #     dimension_id=ENS_MEMBER_DIMNAME,
    #     start_time=None,
    # ):
    #     # Puts a single ensemble member forecasts for all stations into a netCDF file
    #     raise NotImplementedError

    # def put_ensemble_series(
    #     self,
    #     x,
    #     variable_name="rain_ens",
    #     identifier: str = None,
    #     dimension_id=None,
    # ):
    #     # Puts an ensemble of time series, e.g. replicate rainfall series
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     raise NotImplementedError

    # def put_single_series(
    #     self,
    #     x,
    #     variable_name="rain_obs",
    #     identifier: str = None,
    #     dimension_id=None,
    #     start_time=None,
    # ):
    #     # Puts a time series, or part thereof
    #     if dimension_id is None:
    #         dimension_id = self.get_stations_varname()
    #     raise NotImplementedError

    # def put_values(self, x, variable_name):
    #     # Puts all the values in a variable. Should be used only for dimension variables
    #     raise NotImplementedError

    # def set_time_zone(self, tzone_id):
    #     # Sets the time zone to use for the read time series
    #     raise NotImplementedError

    # def summary(self):
    #     # Print a summary of this EFTS netCDF file
    #     raise NotImplementedError

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
#' (stations_ids = snc$get_values(STATION_ID_DIMNAME))
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
def open_efts(ncfile: Any, writein: bool = False) -> EftsDataSet:  # noqa: ARG001, FBT001, FBT002
    """Open an EFTS NetCDF file."""
    # raise NotImplemented("open_efts")
    # if isinstance(ncfile, str):
    #     nc = ncdf4::nc_open(ncfile, readunlim = FALSE, write = writein)
    # } else if (methods::is(ncfile, "ncdf4")) {
    #     nc = ncfile
    # }
    return EftsDataSet(ncfile)


def nan_full(shape: Union[Tuple, int]) -> np.ndarray:
    """Create a full array of NaNs with the given shape."""
    if isinstance(shape, int):
        shape = (shape,)
    return np.full(shape=shape, fill_value=np.nan)


def xr_efts(
    issue_times: Iterable[ConvertibleToTimestamp],
    station_ids: Iterable[str],
    lead_times: Optional[Iterable[int]] = None,
    lead_time_tstep: str = "hours",
    ensemble_size: int = 1,
    # variables
    station_names: Optional[Iterable[str]] = None,
    latitudes: Optional[Iterable[float]] = None,
    longitudes: Optional[Iterable[float]] = None,
    areas: Optional[Iterable[float]] = None,
    nc_attributes: Optional[Dict[str, str]] = None,
) -> xr.Dataset:
    """Create an xarray Dataset for EFTS data."""
    # Check that station ids are unique:
    if len(set(station_ids)) != len(station_ids):
        raise ValueError("Station names must be unique.")
    # I learned today that xarray 2025.7.1 can accept pandas datetimeindex as coordinates
    # See https://github.com/csiro-hydroinformatics/efts-io/issues/13, in the future may change design.
    if isinstance(issue_times, pd.DatetimeIndex):
        # This will convert each item to a tstamp such as
        # Timestamp('2023-01-01 00:00:00+1000', tz='UTC+10:00')
        issue_times = list(issue_times)  # issue_times is iterable,and iterated over indeed.
    if lead_times is None:
        lead_times = [0]
    coords = {
        TIME_DIMNAME: issue_times,
        # STATION_DIMNAME: np.arange(start=1, stop=len(station_ids) + 1, step=1),
        STATION_ID_DIMNAME: station_ids,  # np.arange(start=1, stop=len(station_ids) + 1, step=1),
        REALISATION_DIMNAME: np.arange(start=1, stop=ensemble_size + 1, step=1),
        LEAD_TIME_DIMNAME: lead_times,
        # Initially, I was exploring attaching a coordinate to an existing dimension STATION_DIMNAME, using:
        # https://docs.xarray.dev/en/latest/generated/xarray.DataArray.assign_coords.html#xarray.DataArray.assign_coords
        # then using https://github.com/pydata/xarray/issues/2028#issuecomment-1265252754  to be able to
        # index by station IDs. But in July 2025 decided to not have a STATION_DIMNAME dimension, which is
        # an artefact from legacy conventions (Fortran 1-based indexing and other related limitations).
        # Keeping a number based STATION_DIMNAME here is only making things more difficult and data subsetting more prone to bugs.
        # STATION_ID_VARNAME: (STATION_DIMNAME, station_ids),
    }
    n_stations = len(station_ids)
    latitudes = latitudes if latitudes is not None else nan_full(n_stations)
    longitudes = longitudes if longitudes is not None else nan_full(n_stations)
    areas = areas if areas is not None else nan_full(n_stations)
    station_names = station_names if station_names is not None else [f"{i}" for i in station_ids]
    data_vars = {
        STATION_NAME_VARNAME: (STATION_ID_DIMNAME, station_names),
        LAT_VARNAME: (STATION_ID_DIMNAME, latitudes),
        LON_VARNAME: (STATION_ID_DIMNAME, longitudes),
        AREA_VARNAME: (STATION_ID_DIMNAME, areas),
    }
    nc_attributes = nc_attributes or _stf2_mandatory_global_attributes()
    d = xr.Dataset(
        data_vars=data_vars,
        coords=coords,
        attrs=nc_attributes,
    )
    # Credits to the work reported in https://github.com/pydata/xarray/issues/2028#issuecomment-1265252754
    # d = d.set_xindex(STATION_ID_VARNAME)
    d.time.attrs = {
        STANDARD_NAME_ATTR_KEY: TIME_DIMNAME,
        LONG_NAME_ATTR_KEY: TIME_DIMNAME,
        # TIME_STANDARD_KEY: "UTC",
        AXIS_ATTR_KEY: "t",
        # UNITS_ATTR_KEY: "days since 2000-11-14 23:00:00.0 +0000",
    }
    d.lead_time.attrs = {
        STANDARD_NAME_ATTR_KEY: "lead time",
        LONG_NAME_ATTR_KEY: "forecast lead time",
        AXIS_ATTR_KEY: "v",
        UNITS_ATTR_KEY: f"{lead_time_tstep} since time",
    }
    d.realisation.attrs = {
        STANDARD_NAME_ATTR_KEY: ENS_MEMBER_DIMNAME,  # TODO: should we keep the STF 2.0 ens_member as a standard name?
        LONG_NAME_ATTR_KEY: "ensemble member",
        UNITS_ATTR_KEY: "member id",
        AXIS_ATTR_KEY: "u",
    }
    d.station_id.attrs = {LONG_NAME_ATTR_KEY: "station or node identification code"}
    d.station_name.attrs = {LONG_NAME_ATTR_KEY: "station or node name"}
    d.lat.attrs = {LONG_NAME_ATTR_KEY: "latitude", UNITS_ATTR_KEY: "degrees_north", AXIS_ATTR_KEY: "y"}
    d.lon.attrs = {LONG_NAME_ATTR_KEY: "longitude", UNITS_ATTR_KEY: "degrees_east", AXIS_ATTR_KEY: "x"}
    d.area.attrs = {
        LONG_NAME_ATTR_KEY: "station area",
        UNITS_ATTR_KEY: "km^2",
        STANDARD_NAME_ATTR_KEY: AREA_VARNAME,
    }
    return d


def _stf2_mandatory_global_attributes(
    title: str = "not provided",
    institution: str = "not provided",
    catchment: str = "not provided",
    source: str = "not provided",
    comment: str = "not provided",
    history: str = "not provided",
) -> Dict[str, str]:
    """Create a dictionary of mandatory global attributes for an EFTS dataset."""
    return {
        TITLE_ATTR_KEY: title,
        INSTITUTION_ATTR_KEY: institution,
        CATCHMENT_ATTR_KEY: catchment,
        SOURCE_ATTR_KEY: source,
        COMMENT_ATTR_KEY: comment,
        HISTORY_ATTR_KEY: history,
        STF_CONVENTION_VERSION_ATTR_KEY: "2.0",
        STF_NC_SPEC_ATTR_KEY: STF_2_0_URL,
    }


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
#' snc$put_values(letters[1:2], STATION_NAME_VARNAME)
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
    data_var_definitions: List[Dict[str, Any]],
    stations_ids: List[int],
    station_names: Optional[List[str]] = None,  # noqa: ARG001
    nc_attributes: Optional[Dict[str, str]] = None,
    optional_vars: Optional[dict[str, Any]] = None,
    lead_length: int = 48,
    ensemble_length: int = 50,
    lead_time_tstep: str = "hours",
) -> EftsDataSet:
    """Create a new EFTS dataset."""
    import xarray as xr

    from efts_io.conventions import mandatory_global_attributes

    if stations_ids is None:
        raise ValueError(
            "You must provide station identifiers when creating a new EFTS netCDF data set",
        )

    if nc_attributes is None:
        raise ValueError(
            "You must provide a suitable list for nc_attributes, including" + ", ".join(mandatory_global_attributes),
        )

    # check_global_attributes(nc_attributes)

    if os.path.exists(fname):
        raise FileExistsError("File already exists: " + fname)

    if isinstance(data_var_definitions, pd.DataFrame):
        raise TypeError(
            "data_var_definitions should be a list of dictionaries, not a pandas DataFrame",
        )

    var_defs = create_efts_variables(
        data_var_definitions,
        time_dim_info,
        num_stations=len(stations_ids),
        lead_length=lead_length,
        ensemble_length=ensemble_length,
        optional_vars=optional_vars,
        lead_time_tstep=lead_time_tstep,
    )

    ## attributes for dimensions variables
    def add_dim_attribute(v: xr.Variable, dimname: str, attr_key: str, attr_value: str) -> None:
        pass

    add_dim_attribute(var_defs, TIME_DIMNAME, STANDARD_NAME_ATTR_KEY, TIME_DIMNAME)
    add_dim_attribute(var_defs, TIME_DIMNAME, TIME_STANDARD_ATTR_KEY, "UTC")
    add_dim_attribute(var_defs, TIME_DIMNAME, AXIS_ATTR_KEY, "t")
    add_dim_attribute(var_defs, ENS_MEMBER_DIMNAME, STANDARD_NAME_ATTR_KEY, ENS_MEMBER_DIMNAME)
    add_dim_attribute(var_defs, ENS_MEMBER_DIMNAME, AXIS_ATTR_KEY, "u")
    add_dim_attribute(var_defs, LEAD_TIME_DIMNAME, STANDARD_NAME_ATTR_KEY, LEAD_TIME_DIMNAME)
    add_dim_attribute(var_defs, LEAD_TIME_DIMNAME, AXIS_ATTR_KEY, "v")
    add_dim_attribute(var_defs, LAT_VARNAME, AXIS_ATTR_KEY, "y")
    add_dim_attribute(var_defs, LON_VARNAME, AXIS_ATTR_KEY, "x")

    d = xr.Dataset(
        data_vars=var_defs["datavars"],
        coords=var_defs["metadatavars"],
        attrs={"description": "TODO: put the right attributes"},
    )

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
#   ncdf4::ncatt_put(nc, TIME_DIMNAME, STANDARD_NAME_KEY, TIME_DIMNAME)
#   ncdf4::ncatt_put(nc, TIME_DIMNAME, TIME_STANDARD_KEY, "UTC")
#   ncdf4::ncatt_put(nc, TIME_DIMNAME, AXIS_ATTR_KEY, "t")
#   ncdf4::ncatt_put(nc, ENS_MEMBER_DIMNAME, STANDARD_NAME_KEY, ENS_MEMBER_DIMNAME)
#   ncdf4::ncatt_put(nc, ENS_MEMBER_DIMNAME, AXIS_ATTR_KEY, "u")
#   ncdf4::ncatt_put(nc, LEAD_TIME_DIMNAME, STANDARD_NAME_KEY, LEAD_TIME_DIMNAME)
#   ncdf4::ncatt_put(nc, LEAD_TIME_DIMNAME, AXIS_ATTR_KEY, "v")
#   ncdf4::ncatt_put(nc, LAT_VARNAME, AXIS_ATTR_KEY, "y")
#   ncdf4::ncatt_put(nc, lon_varname, AXIS_ATTR_KEY, "x")

#   ## attributes for optional metadata variables
#   if(!is.None(optional_vars))
#   {
#     var_names = rownames(optional_vars)
#     if(STANDARD_NAME_KEY %in% colnames(optional_vars)){
#       for (v in var_names) {
#         sn = optional_vars[v, STANDARD_NAME_KEY]
#         if(!is.na(sn)) ncdf4::ncatt_put(nc, v, STANDARD_NAME_KEY, sn)
#       }
#     }
#     if(x_varname %in% var_names){
#       ncdf4::ncatt_put(nc, x_varname, AXIS_ATTR_KEY, "x")
#     }
#     if(y_varname %in% var_names){
#       ncdf4::ncatt_put(nc, y_varname, AXIS_ATTR_KEY, "y")
#     }
#   }

#   ## Add global attributes
#   ncdf4::ncatt_put(nc, 0, STF_CONVENTION_VERSION_ATTR_KEY, 2)
#   ncdf4::ncatt_put(nc, 0, STF_NC_SPEC_ATTR_KEY, "https://github.com/jmp75/efts/blob/107c553045a37e6ef36b2eababf6a299e7883d50/docs/netcdf_for_water_forecasting.md")
#   ncdf4::ncatt_put(nc, 0, HISTORY_ATTR_KEY,
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
#   ncdf4::ncvar_put(nc, STATION_ID_VARNAME, stations_ids)
#   ncdf4::ncvar_put(nc, LEAD_TIME_DIMNAME, 1:lead_length)
#   ncdf4::ncvar_put(nc, ENS_MEMBER_DIMNAME, 1:ensemble_length)
#   if (!is.None(station_names)) {
#     ncdf4::ncvar_put(nc, STATION_NAME_VARNAME, station_names)
#   }
#   # One seems to need to close/reopen the newly created file, otherwise some
#   # ncvar_get operations will fail with a cryptic message.  I follow the
#   # advice in this and associated posts
#   # https://www.unidata.ucar.edu/mailing_lists/archives/netcdfgroup/2012/msg00270.html
#   ncdf4::nc_close(nc)
#   nc = ncdf4::nc_open(fname, write = TRUE, readunlim = FALSE)
#   return(nc)
# }
