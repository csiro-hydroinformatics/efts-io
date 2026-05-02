"""A thin wrapper around xarray for reading and writing Ensemble Forecast Time Series (EFTS) data sets."""

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

# import netCDF4
import numpy as np
import pandas as pd
import xarray as xr

from efts_io._ncdf_stf2 import StfVariable
from efts_io.conventions import (
    AREA_VARNAME,
    AXIS_ATTR_KEY,
    CATCHMENT_ATTR_KEY,
    COMMENT_ATTR_KEY,
    ENS_MEMBER_DIMNAME,
    FILLVALUE_ATTR_KEY,
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
    DataOriginType,
)
from efts_io.dimensions import cftimes_to_pdtstamps


def byte_to_string(x: int | bytes) -> str:
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
    from xarray.coding import times  # noqa: PLC0415

    # work around https://jira.csiro.au/browse/WIRADA-635
    # lead_time can be a problem with xarray, so do not decode "times"
    # we also use mask_and_scale=False because of https://github.com/csiro-hydroinformatics/efts-io/issues/24
    x = xr.open_dataset(file_path, decode_times=False, mask_and_scale=False)
    # replace the time and station names coordinates values
    # TODO: This is probably not a long term solution for round-tripping a read/write or vice and versa
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
    # Use np.atleast_1d to handle the case where there's only one station/ensemble/lead_time,
    # which would otherwise result in a 0-dimensional array that xarray cannot use as a coordinate.
    station_ids_strings = np.atleast_1d(x[STATION_ID_VARNAME].values.astype(np.str_))  # noqa: PD011
    ens_member_values = np.atleast_1d(x[ENS_MEMBER_DIMNAME].values)
    lead_time_values = np.atleast_1d(x[LEAD_TIME_DIMNAME].values)
    # x = x.assign_coords(
    #     {TIME_DIMNAME: time_coords, self.STATION_DIMNAME: station_names},
    # )

    lead_time_attrs = dict(x[LEAD_TIME_DIMNAME].attrs)
    # Create a new dataset with the desired structure
    new_dataset = xr.Dataset(
        coords={
            LEAD_TIME_DIMNAME: (LEAD_TIME_DIMNAME, lead_time_values),
            REALISATION_DIMNAME: (REALISATION_DIMNAME, ens_member_values),
            STATION_ID_DIMNAME: (STATION_ID_DIMNAME, station_ids_strings),
            TIME_DIMNAME: (TIME_DIMNAME, time_coords),
        },
        attrs=x.attrs,
    )
    new_dataset[LEAD_TIME_DIMNAME].attrs = lead_time_attrs
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
        data=station_names_var.values.astype(np.str_),  # noqa: PD011
        dims=[STATION_ID_DIMNAME],
        coords={STATION_ID_DIMNAME: new_dataset[STATION_ID_DIMNAME]},
        attrs=station_names_var.attrs,
    )
    return new_dataset


class EftsDataSet:
    """Convenience class for access to a Ensemble Forecast Time Series in netCDF file."""
    def __init__(self, data: str | xr.Dataset) -> None:
        """Create a new EftsDataSet object."""
        self.time_zone_timestamps = True  # Not sure about https://github.com/csiro-hydroinformatics/efts-io/issues/3
        self.STATION_DIMNAME = STATION_DIMNAME
        self.stations_varname = STATION_ID_VARNAME
        self.LEAD_TIME_DIMNAME = LEAD_TIME_DIMNAME
        self.ENS_MEMBER_DIMNAME = ENS_MEMBER_DIMNAME
        self.data: xr.Dataset

        if data is None:
            raise ValueError("input cannot be None")
        if isinstance(data, Path):
            data = str(data)
        if isinstance(data, str):
            new_dataset = load_from_stf2_file(data, self.time_zone_timestamps)
            self.data = new_dataset
        elif isinstance(data, xr.Dataset):
            self.data = data
        else:
            raise TypeError(f"Unsupported type {type(data)}")

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

    def append_history(self, message: str, timestamp: datetime | None = None) -> None:
        """Append a new entry to the `history` attribute with a timestamp.

        message: The message to append.
        timestamp: If not provided, the current UTC time is used.
        """
        from datetime import UTC  # noqa: PLC0415

        if timestamp is None:
            timestamp = datetime.now(UTC)
        ts_str = timestamp.isoformat()

        current_history = self.data.attrs.get(HISTORY_ATTR_KEY, "")
        if current_history:
            self.data.attrs[HISTORY_ATTR_KEY] = f"{current_history}\n{ts_str} - {message}"
        else:
            self.data.attrs[HISTORY_ATTR_KEY] = f"{ts_str} - {message}"

    def to_netcdf(self, path: str, version: str | None = "2.0") -> None:
        """Write the data set to a netCDF file.

        If version is "2.0", the dataset is written using the save_to_stf2 method, which ensures
        compliance with the STF 2.0 specification. Only version "2.0" is currently supported.
        If version is None, the dataset is written using xarray's built-in to_netcdf method,
        which may not be compliant with any specific convention.

        Args:
            path (str): The file path to write the netCDF file to.
            version (str | None, optional): The version of the netCDF format to write. Defaults to "2.0". If None, uses xarray's default writing method.
        """
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
        from efts_io.conventions import exportable_to_stf2  # noqa: PLC0415

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
        variable_name: str | None = None,
        var_type: StfVariable = StfVariable.STREAMFLOW,
        data_type: DataOriginType = DataOriginType.OBSERVED,
        ens: bool = False,  # noqa: FBT001, FBT002
        timestep: str = "days",
        data_qual: xr.DataArray | None = None,
    ) -> None:
        """Save to file."""
        from efts_io._ncdf_stf2 import write_nc_stf2  # noqa: PLC0415

        if isinstance(self.data, xr.Dataset):
            if variable_name is None:
                raise ValueError("Inner data is a DataSet, so an explicit variable name must be explicitely specified.")
            d = self.data[variable_name]
        # elif isinstance(self.data, xr.DataArray):
        #    d = self.data
        else:
            raise TypeError(f"Unsupported data type {type(self.data)}")

        if UNITS_ATTR_KEY not in d.attrs:
            raise ValueError(f"DataArray variable '{d.name}' must have '{UNITS_ATTR_KEY}' attribute defined.")

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

    def create_data_variables(self, data_var_def: dict[str, dict[str, Any]]) -> None:
        """Create data variables in the data set.

        var_defs_dict["variable_1"].keys()
        dict_keys(['name', 'longname', 'units', 'dim_type', 'missval', 'precision', 'attributes'])
        """
        ens_fcast_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "4"]
        ens_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "3"]
        point_data_var_def = [x for x in data_var_def.values() if x["dim_type"] == "2"]

        # Dimension order follows C (row-major) convention: slowest-varying axis first, fastest last.
        # The STF 2.0 specification lists dimensions in Fortran order
        # (lead_time, station, ens_member, time), but Python/NumPy arrays are C-order.
        # Both the on-disk write path (make_ready_for_saving) and the read path
        # (load_from_stf2_file) use C order: (time, realization, station_id, lead_time).
        # Using the same order here ensures freshly created variables are laid out
        # identically to variables reconstructed after a save/reload cycle, preventing
        # silent axis-mismatch bugs when indexing with positional notation.
        four_dims_names = (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
        three_dims_names = (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME)
        two_dims_names = (TIME_DIMNAME, STATION_ID_DIMNAME)

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
                # TODO: perhaps check for keys here
                # _check_mandatory_keys(x)
                self._new_variable_from_legacy_specs(dims_shape, dims_names, x, varname)

    def _new_variable_from_legacy_specs(
        self,
        dim_shape: tuple,
        dims_names: Iterable[str],
        x: dict[str, Any],
        varname: str,
    ) -> xr.DataArray:
        """Create a new variable in the data set."""
        data_coords = {dim: self.data.coords[dim] for dim in dims_names}
        new_array = xr.DataArray(
            name=varname,
            data=nan_full(dim_shape),
            coords=data_coords,
            dims=dims_names,
            attrs={
                LONG_NAME_ATTR_KEY: x["longname"],
                UNITS_ATTR_KEY: x[UNITS_ATTR_KEY],
                FILLVALUE_ATTR_KEY: x["missval"],
                "precision": x["precision"],  # TODO: check whether this is still of use.
                **x["attributes"],
            },
        )
        self.data[varname] = new_array
        return new_array

    def new_variable(
        self,
        varname: str,
        dim_names: Iterable[str],
        var_attributes: dict[str, Any],
        data: np.ndarray | None = None,
    ) -> xr.DataArray:
        """Create a new variable in the data set.

        Args:
            varname (str): Name of the new variable.
            dim_names (Iterable[str]): Names of the dimensions for the new variable.
            var_attributes (dict[str, Any]): Attributes for the new variable. Must include 'units' key. See `template_variable_attributes`
            data (Optional[np.ndarray], optional): Data for the new variable. If None, the variable is initialized with NaNs. Defaults to None.

        Returns:
            xr.DataArray: The newly created variable as an xarray DataArray.
        """
        if varname in self.data.variables:
            raise ValueError(f"Variable '{varname}' already exists in the dataset.")
        if UNITS_ATTR_KEY not in var_attributes:
            raise ValueError(f"Variable attributes must include '{UNITS_ATTR_KEY}' key.")
        known_dimnames = self.get_dim_names()
        unknown_dims = [x for x in dim_names if x not in set(known_dimnames)]
        if unknown_dims:
            raise ValueError(f"Unknown dimension names: {unknown_dims}; must be one of {known_dimnames}.")
        dims_shape = tuple(self.data.sizes[dimname] for dimname in dim_names)
        if data is not None:
            if data.shape != dims_shape:
                raise ValueError(
                    f"Data shape {data.shape} does not match expected shape {dims_shape} for dimensions {dim_names}.",
                )
            data_array = data
        else:
            data_array = nan_full(dims_shape)
        data_coords = {dim: self.data.coords[dim] for dim in dim_names}
        new_array = xr.DataArray(
            name=varname,
            data=data_array,
            coords=data_coords,
            dims=dim_names,
            attrs=var_attributes.copy(),
        )
        self.data[varname] = new_array
        return new_array

    def get_all_series(
        self,
        variable_name: str = "rain_obs",
        dimension_id: str | None = None,  # noqa: ARG002
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

    def get_dim_names(self) -> list[str]:
        """Gets the name of all dimensions in the data set."""
        return [x for x in self.data.sizes.keys()]  # noqa: C416, SIM118
        # Note: self._dim_size will return a list of str in the future
        # return [x for x in self._dim_size.keys()]

    def get_ensemble_for_stations(
        self,
        variable_name: str = "rain_sim",
        identifier: str | None = None,
        dimension_id: str = ENS_MEMBER_DIMNAME,
        start_time: pd.Timestamp = None,
        lead_time_count: int | None = None,
    ) -> xr.DataArray:
        """Not yet implemented."""
        # Return a time series, representing a single ensemble member forecast for all stations over the lead time
        raise NotImplementedError

    def get_ensemble_forecasts(
        self,
        variable_name: str = "rain_sim",
        identifier: str | None = None,
        dimension_id: str | None = None,
        start_time: pd.Timestamp | None = None,
        lead_time_count: int | None = None,
    ) -> xr.DataArray:
        """Not yet implemented. Gets an ensemble forecast for a variable."""
        # Return a time series, ensemble of forecasts over the lead time
        raise NotImplementedError(
            "get_ensemble_forecasts: not yet implemented",
        )

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
        return self._dim_size(REALISATION_DIMNAME)

    def get_lead_time_count(self) -> int:
        """Length of the lead time dimension."""
        return self._dim_size(self.LEAD_TIME_DIMNAME)

    def get_lead_time_values(self) -> np.ndarray:
        """Return the values of the lead time dimension."""
        return self.data[self.LEAD_TIME_DIMNAME].to_numpy()

    def put_lead_time_values(self, values: Iterable[float]) -> None:
        """Set the values of the lead time dimension."""
        self.data[self.LEAD_TIME_DIMNAME].values = np.array(values)

    def get_single_series(
        self,
        variable_name: str = "rain_obs",
        identifier: str | None = None,
        dimension_id: str | None = None,
    ) -> xr.DataArray:
        """Return a single point time series for a station identifier."""
        # Return a single point time series for a station identifier. Falls back on def get_all_series if the argument "identifier" is missing
        if dimension_id is None:
            dimension_id = self.get_stations_varname()
        return self.data[variable_name].sel({dimension_id: identifier})

    def get_station_count(self) -> int:
        """Return the number of stations in the data set."""
        return self._dim_size(STATION_ID_DIMNAME)

    def get_stations_varname(self) -> str:
        """Return the name of the variable that has the station identifiers."""
        # Gets the name of the variable that has the station identifiers
        # TODO: station is integer normally in STF (Euargh)
        return STATION_ID_VARNAME

    def get_time_dim(self) -> np.ndarray:
        """Return the time dimension variable as a vector of date-time stamps."""
        # Gets the time dimension variable as a vector of date-time stamps
        return self.data.time.to_numpy()  # but loosing attributes.

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
def open_efts(ncfile: Any) -> EftsDataSet:
    """Open an EFTS NetCDF file."""
    # raise NotImplemented("open_efts")
    # if isinstance(ncfile, str):
    #     nc = ncdf4::nc_open(ncfile, readunlim = FALSE, write = writein)
    # } else if (methods::is(ncfile, "ncdf4")) {
    #     nc = ncfile
    # }
    return EftsDataSet(ncfile)


def nan_full(shape: tuple | int) -> np.ndarray:
    """Create a full array of NaNs with the given shape."""
    if isinstance(shape, int):
        shape = (shape,)
    return np.full(shape=shape, fill_value=np.nan)


def xr_efts(
    issue_times: Iterable[ConvertibleToTimestamp],
    station_ids: Iterable[str],
    lead_times: Iterable[int] | None = None,
    lead_time_tstep: str = "hours",
    ensemble_size: int = 1,
    # variables
    station_names: Iterable[str] | None = None,
    latitudes: Iterable[float] | None = None,
    longitudes: Iterable[float] | None = None,
    areas: Iterable[float] | None = None,
    nc_attributes: dict[str, str] | None = None,
) -> xr.Dataset:
    """Create an xarray Dataset for EFTS data."""
    # Check that station ids are unique:
    if len(set(station_ids)) != len(station_ids):
        raise ValueError("Station names must be unique.")
    # I learned today that xarray 2025.7.1 can now accept pandas datetimeindex as coordinates
    # for backward compatibility with older xarray versions, we convert to list here.
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
    d.realization.attrs = {
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


def create_mandatory_global_attributes(
    title: str,
    institution: str,
    catchment: str,
    source: str,
    comment: str,
    history: str | None = None,
) -> dict[str, str]:
    """Create a dictionary of mandatory global attributes for an EFTS dataset.

    Args:
        title (str): Title of the dataset.
        institution (str): Institution responsible for the dataset.
        catchment (str): Catchment area description.
        source (str): Source of the data.
        comment (str): Additional comments about the dataset.
        history (Optional[str], optional): History of the dataset. If None, a default history message is created. Defaults to None.

    Returns:
        Dict[str, str]: A dictionary containing the mandatory global attributes.
    """
    d = _stf2_mandatory_global_attributes(
        title=title,
        institution=institution,
        catchment=catchment,
        source=source,
        comment=comment,
        history=history or __default_history_attval(),
    )
    return d  # noqa: RET504


def __default_history_attval() -> str:
    try:
        from importlib.metadata import version  # noqa: PLC0415

        pkg_version = version("efts-io")
    except Exception:  # noqa: BLE001
        pkg_version = "unknown"
    return f"Created on {pd.Timestamp.now(tz='UTC').isoformat()} by efts-io v{pkg_version}"


def _stf2_mandatory_global_attributes(
    title: str = "not provided",
    institution: str = "not provided",
    catchment: str = "not provided",
    source: str = "not provided",
    comment: str = "not provided",
    history: str = "not provided",
) -> dict[str, str]:
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
