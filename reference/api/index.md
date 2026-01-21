## API reference for `efts-io`

# wrapper

A thin wrapper around xarray for reading and writing Ensemble Forecast Time Series (EFTS) data sets.

Classes:

- **`EftsDataSet`** – Convenience class for access to a Ensemble Forecast Time Series in netCDF file.

Functions:

- **`byte_array_to_string`** – Convert a byte array to a string.
- **`byte_stations_to_str`** – Convert byte array of station names to string array.
- **`byte_to_string`** – Convert a byte to a string.
- **`create_efts`** – Create a new EFTS dataset.
- **`load_from_stf2_file`** – Load data from an STF 2.0 netcdf file to an xarray representation.
- **`nan_full`** – Create a full array of NaNs with the given shape.
- **`open_efts`** – Open an EFTS NetCDF file.
- **`xr_efts`** – Create an xarray Dataset for EFTS data.

## EftsDataSet

```
EftsDataSet(data: Union[str, Dataset])
```

Convenience class for access to a Ensemble Forecast Time Series in netCDF file.

Methods:

- **`append_history`** – Append a new entry to the history attribute with a timestamp.
- **`create_data_variables`** – Create data variables in the data set.
- **`get_all_series`** – Return a multivariate time series, where each column is the series for one of the identifiers.
- **`get_dim_names`** – Gets the name of all dimensions in the data set.
- **`get_ensemble_for_stations`** – Not yet implemented.
- **`get_ensemble_forecasts`** – Gets an ensemble forecast for a variable.
- **`get_ensemble_size`** – Return the length of the ensemble size dimension.
- **`get_lead_time_count`** – Length of the lead time dimension.
- **`get_lead_time_values`** – Return the values of the lead time dimension.
- **`get_single_series`** – Return a single point time series for a station identifier.
- **`get_station_count`** – Return the number of stations in the data set.
- **`get_stations_varname`** – Return the name of the variable that has the station identifiers.
- **`get_time_dim`** – Return the time dimension variable as a vector of date-time stamps.
- **`new_variable`** – Create a new variable in the data set.
- **`put_lead_time_values`** – Set the values of the lead time dimension.
- **`save_to_stf2`** – Save to file.
- **`set_mandatory_global_attributes`** – Sets mandatory global attributes for an EFTS dataset.
- **`template_variable_attributes`** – Return a template dictionary for variable attributes.
- **`to_netcdf`** – Write the data set to a netCDF file.
- **`writeable_to_stf2`** – Check if the dataset can be written to a netCDF file compliant with STF 2.0 specification.

Attributes:

- **`catchment`** (`str`) – Get or set the catchment attribute of the dataset.
- **`comment`** (`str`) – Get or set the comment attribute of the dataset.
- **`history`** (`str`) – Gets/sets the history attribute of the dataset.
- **`institution`** (`str`) – Get or set the institution attribute of the dataset.
- **`source`** (`str`) – Get or set the source attribute of the dataset.
- **`stf2_int_datatype`** (`str`) – The type of integer to save to in the STF 2.x netcdf convention: 'i4' or 'i8'.
- **`stf_convention_version`** (`float`) – Get or set the STF_convention_version attribute of the dataset.
- **`stf_nc_spec`** (`str`) – Get or set the STF_nc_spec attribute of the dataset.
- **`title`** (`str`) – Get or set the title attribute of the dataset.

Source code in `src/efts_io/wrapper.py`

```
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
    from pathlib import Path

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
```

### catchment

```
catchment: str
```

Get or set the catchment attribute of the dataset.

### comment

```
comment: str
```

Get or set the comment attribute of the dataset.

### history

```
history: str
```

Gets/sets the history attribute of the dataset.

### institution

```
institution: str
```

Get or set the institution attribute of the dataset.

### source

```
source: str
```

Get or set the source attribute of the dataset.

### stf2_int_datatype

```
stf2_int_datatype: str
```

The type of integer to save to in the STF 2.x netcdf convention: 'i4' or 'i8'.

### stf_convention_version

```
stf_convention_version: float
```

Get or set the STF_convention_version attribute of the dataset.

### stf_nc_spec

```
stf_nc_spec: str
```

Get or set the STF_nc_spec attribute of the dataset.

### title

```
title: str
```

Get or set the title attribute of the dataset.

### append_history

```
append_history(
    message: str, timestamp: Optional[datetime] = None
) -> None
```

Append a new entry to the `history` attribute with a timestamp.

message: The message to append. timestamp: If not provided, the current UTC time is used.

Source code in `src/efts_io/wrapper.py`

```
def append_history(self, message: str, timestamp: Optional[datetime] = None) -> None:
    """Append a new entry to the `history` attribute with a timestamp.

    message: The message to append.
    timestamp: If not provided, the current UTC time is used.
    """
    from datetime import UTC

    if timestamp is None:
        timestamp = datetime.now(UTC).isoformat()

    current_history = self.data.attrs.get(HISTORY_ATTR_KEY, "")
    if current_history:
        self.data.attrs[HISTORY_ATTR_KEY] = f"{current_history}\n{timestamp} - {message}"
    else:
        self.data.attrs[HISTORY_ATTR_KEY] = f"{timestamp} - {message}"
```

### create_data_variables

```
create_data_variables(
    data_var_def: Dict[str, Dict[str, Any]],
) -> None
```

Create data variables in the data set.

var_defs_dict["variable_1"].keys() dict_keys(['name', 'longname', 'units', 'dim_type', 'missval', 'precision', 'attributes'])

Source code in `src/efts_io/wrapper.py`

```
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
            # TODO:
            # _check_mandatory_keys(x)
            self._new_variable_from_legacy_specs(dims_shape, dims_names, x, varname)
```

### get_all_series

```
get_all_series(
    variable_name: str = "rain_obs",
    dimension_id: Optional[str] = None,
) -> DataArray
```

Return a multivariate time series, where each column is the series for one of the identifiers.

Source code in `src/efts_io/wrapper.py`

```
def get_all_series(
    self,
    variable_name: str = "rain_obs",
    dimension_id: Optional[str] = None,  # noqa: ARG002
) -> xr.DataArray:
    """Return a multivariate time series, where each column is the series for one of the identifiers."""
    # Return a multivariate time series, where each column is the series for one of the identifiers (self, e.g. rainfall station identifiers):
    return self.data[variable_name]
```

### get_dim_names

```
get_dim_names() -> List[str]
```

Gets the name of all dimensions in the data set.

Source code in `src/efts_io/wrapper.py`

```
def get_dim_names(self) -> List[str]:
    """Gets the name of all dimensions in the data set."""
    return [x for x in self.data.sizes.keys()]  # noqa: C416, SIM118
```

### get_ensemble_for_stations

```
get_ensemble_for_stations(
    variable_name: str = "rain_sim",
    identifier: Optional[str] = None,
    dimension_id: str = ENS_MEMBER_DIMNAME,
    start_time: Timestamp = None,
    lead_time_count: Optional[int] = None,
) -> DataArray
```

Not yet implemented.

Source code in `src/efts_io/wrapper.py`

```
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
```

### get_ensemble_forecasts

```
get_ensemble_forecasts(
    variable_name: str = "rain_sim",
    identifier: Optional[str] = None,
    dimension_id: Optional[str] = None,
    start_time: Optional[Timestamp] = None,
    lead_time_count: Optional[int] = None,
) -> DataArray
```

Gets an ensemble forecast for a variable.

Source code in `src/efts_io/wrapper.py`

```
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
```

### get_ensemble_size

```
get_ensemble_size() -> int
```

Return the length of the ensemble size dimension.

Source code in `src/efts_io/wrapper.py`

```
def get_ensemble_size(self) -> int:
    """Return the length of the ensemble size dimension."""
    return self._dim_size(self.ENS_MEMBER_DIMNAME)
```

### get_lead_time_count

```
get_lead_time_count() -> int
```

Length of the lead time dimension.

Source code in `src/efts_io/wrapper.py`

```
def get_lead_time_count(self) -> int:
    """Length of the lead time dimension."""
    return self._dim_size(self.LEAD_TIME_DIMNAME)
```

### get_lead_time_values

```
get_lead_time_values() -> ndarray
```

Return the values of the lead time dimension.

Source code in `src/efts_io/wrapper.py`

```
def get_lead_time_values(self) -> np.ndarray:
    """Return the values of the lead time dimension."""
    return self.data[self.LEAD_TIME_DIMNAME].values
```

### get_single_series

```
get_single_series(
    variable_name: str = "rain_obs",
    identifier: Optional[str] = None,
    dimension_id: Optional[str] = None,
) -> DataArray
```

Return a single point time series for a station identifier.

Source code in `src/efts_io/wrapper.py`

```
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
```

### get_station_count

```
get_station_count() -> int
```

Return the number of stations in the data set.

Source code in `src/efts_io/wrapper.py`

```
def get_station_count(self) -> int:
    """Return the number of stations in the data set."""
    self._dim_size(self.STATION_DIMNAME)
```

### get_stations_varname

```
get_stations_varname() -> str
```

Return the name of the variable that has the station identifiers.

Source code in `src/efts_io/wrapper.py`

```
def get_stations_varname(self) -> str:
    """Return the name of the variable that has the station identifiers."""
    # Gets the name of the variable that has the station identifiers
    # TODO: station is integer normally in STF (Euargh)
    return STATION_ID_VARNAME
```

### get_time_dim

```
get_time_dim() -> ndarray
```

Return the time dimension variable as a vector of date-time stamps.

Source code in `src/efts_io/wrapper.py`

```
def get_time_dim(self) -> np.ndarray:
    """Return the time dimension variable as a vector of date-time stamps."""
    # Gets the time dimension variable as a vector of date-time stamps
    return self.data.time.values  # but loosing attributes.
```

### new_variable

```
new_variable(
    varname: str,
    dim_names: Iterable[str],
    var_attributes: dict[str, Any],
    data: Optional[ndarray] = None,
) -> DataArray
```

Create a new variable in the data set.

Parameters:

- **`varname`** (`str`) – Name of the new variable.
- **`dim_names`** (`Iterable[str]`) – Names of the dimensions for the new variable.
- **`var_attributes`** (`dict[str, Any]`) – Attributes for the new variable. Must include 'units' key.
- **`data`** (`Optional[ndarray]`, default: `None` ) – Data for the new variable. If None, the variable is initialized with NaNs. Defaults to None.

Returns:

- `DataArray` – xr.DataArray: The newly created variable as an xarray DataArray.

Source code in `src/efts_io/wrapper.py`

```
def new_variable(self, varname:str, dim_names:Iterable[str], var_attributes:dict[str,Any], data:Optional[np.ndarray]=None) -> xr.DataArray:
    """Create a new variable in the data set.

    Args:
        varname (str): Name of the new variable.
        dim_names (Iterable[str]): Names of the dimensions for the new variable.
        var_attributes (dict[str, Any]): Attributes for the new variable. Must include 'units' key.
        data (Optional[np.ndarray], optional): Data for the new variable. If None, the variable is initialized with NaNs. Defaults to None.

    Returns:
        xr.DataArray: The newly created variable as an xarray DataArray.
    """
    if varname in self.data.variables:
        raise ValueError(f"Variable '{varname}' already exists in the dataset.")
    if UNITS_ATTR_KEY not in var_attributes:
        raise ValueError(f"Variable attributes must include '{UNITS_ATTR_KEY}' key.")
    dims_shape = tuple(self.data.sizes[dimname] for dimname in dim_names)
    if data is not None:
        if data.shape != dims_shape:
            raise ValueError(f"Data shape {data.shape} does not match expected shape {dims_shape} for dimensions {dim_names}.")
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
```

### put_lead_time_values

```
put_lead_time_values(values: Iterable[float]) -> None
```

Set the values of the lead time dimension.

Source code in `src/efts_io/wrapper.py`

```
def put_lead_time_values(self, values: Iterable[float]) -> None:
    """Set the values of the lead time dimension."""
    self.data[self.LEAD_TIME_DIMNAME].values = np.array(values)
```

### save_to_stf2

```
save_to_stf2(
    path: str,
    variable_name: Optional[str] = None,
    var_type: StfVariable = STREAMFLOW,
    data_type: StfDataType = OBSERVED,
    ens: bool = False,
    timestep: str = "days",
    data_qual: Optional[DataArray] = None,
) -> None
```

Save to file.

Source code in `src/efts_io/wrapper.py`

```
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
```

### set_mandatory_global_attributes

```
set_mandatory_global_attributes(
    title: str = "not provided",
    institution: str = "not provided",
    catchment: str = "not provided",
    source: str = "not provided",
    comment: str = "not provided",
    history: str = "not provided",
    append_history: bool = False,
) -> None
```

Sets mandatory global attributes for an EFTS dataset.

Source code in `src/efts_io/wrapper.py`

```
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
```

### template_variable_attributes

```
template_variable_attributes() -> dict[str, Any]
```

Return a template dictionary for variable attributes.

Source code in `src/efts_io/wrapper.py`

```
def template_variable_attributes() -> dict[str, Any]:
    """Return a template dictionary for variable attributes."""
    from efts_io.conventions import _template_variable_attributes
    return _template_variable_attributes()
```

### to_netcdf

```
to_netcdf(
    path: str, version: Optional[str] = "2.0"
) -> None
```

Write the data set to a netCDF file.

Source code in `src/efts_io/wrapper.py`

```
def to_netcdf(self, path: str, version: Optional[str] = "2.0") -> None:
    """Write the data set to a netCDF file."""
    if version is None:
        self.data.to_netcdf(path)
    elif version == "2.0":
        self.save_to_stf2(path)
    else:
        raise ValueError("Only version 2.0 is supported for now")
```

### writeable_to_stf2

```
writeable_to_stf2() -> bool
```

Check if the dataset can be written to a netCDF file compliant with STF 2.0 specification.

This method checks if the underlying xarray dataset or dataarray has the required dimensions and global attributes as specified by the STF 2.0 convention.

Returns:

- **`bool`** ( `bool` ) – True if the dataset can be written to a STF 2.0 compliant netCDF file, False otherwise.

Source code in `src/efts_io/wrapper.py`

```
def writeable_to_stf2(self) -> bool:
    """Check if the dataset can be written to a netCDF file compliant with STF 2.0 specification.

    This method checks if the underlying xarray dataset or dataarray has the required dimensions and global attributes as specified by the STF 2.0 convention.

    Returns:
        bool: True if the dataset can be written to a STF 2.0 compliant netCDF file, False otherwise.
    """
    from efts_io.conventions import exportable_to_stf2

    return exportable_to_stf2(self.data)
```

## byte_array_to_string

```
byte_array_to_string(x: ndarray) -> str
```

Convert a byte array to a string.

Source code in `src/efts_io/wrapper.py`

```
def byte_array_to_string(x: np.ndarray) -> str:
    """Convert a byte array to a string."""
    s = "".join([byte_to_string(s) for s in x])
    return s.strip()
```

## byte_stations_to_str

```
byte_stations_to_str(byte_names: ndarray) -> ndarray
```

Convert byte array of station names to string array.

Source code in `src/efts_io/wrapper.py`

```
def byte_stations_to_str(byte_names: np.ndarray) -> np.ndarray:
    """Convert byte array of station names to string array."""
    return np.array([byte_array_to_string(x) for x in byte_names])
```

## byte_to_string

```
byte_to_string(x: Union[int, bytes]) -> str
```

Convert a byte to a string.

Source code in `src/efts_io/wrapper.py`

```
def byte_to_string(x: Union[int, bytes]) -> str:
    """Convert a byte to a string."""
    if isinstance(x, int):
        if x > 255 or x < 0:  # noqa: PLR2004
            raise ValueError("Integer value to bytes: must be in range [0-255]")
        x = x.to_bytes(1, "little")
    if not isinstance(x, bytes):
        raise TypeError(f"Cannot cast type {type(x)} to bytes")
    return str(x, encoding="UTF-8")
```

## create_efts

```
create_efts(
    fname: str,
    time_dim_info: Dict,
    data_var_definitions: List[Dict[str, Any]],
    stations_ids: List[int],
    station_names: Optional[List[str]] = None,
    nc_attributes: Optional[Dict[str, str]] = None,
    optional_vars: Optional[dict[str, Any]] = None,
    lead_length: int = 48,
    ensemble_length: int = 50,
    lead_time_tstep: str = "hours",
) -> EftsDataSet
```

Create a new EFTS dataset.

Source code in `src/efts_io/wrapper.py`

```
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
```

## load_from_stf2_file

```
load_from_stf2_file(
    file_path: str, time_zone_timestamps: bool
) -> Dataset
```

Load data from an STF 2.0 netcdf file to an xarray representation.

Parameters:

- **`file_path`** (`str`) – file path
- **`time_zone_timestamps`** (`bool`) – should we try to recognise the time zone and include it in each xarray time stamp?

Returns:

- **`_type_`** ( `Dataset` ) – xarray Dataset

Source code in `src/efts_io/wrapper.py`

```
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
    # we also use mask_and_scale=False because of https://github.com/csiro-hydroinformatics/efts-io/issues/24
    x = xr.open_dataset(file_path, decode_times=False, mask_and_scale=False)
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
```

## nan_full

```
nan_full(shape: Union[Tuple, int]) -> ndarray
```

Create a full array of NaNs with the given shape.

Source code in `src/efts_io/wrapper.py`

```
def nan_full(shape: Union[Tuple, int]) -> np.ndarray:
    """Create a full array of NaNs with the given shape."""
    if isinstance(shape, int):
        shape = (shape,)
    return np.full(shape=shape, fill_value=np.nan)
```

## open_efts

```
open_efts(
    ncfile: Any, writein: bool = False
) -> EftsDataSet
```

Open an EFTS NetCDF file.

Source code in `src/efts_io/wrapper.py`

```
def open_efts(ncfile: Any, writein: bool = False) -> EftsDataSet:  # noqa: ARG001, FBT001, FBT002
    """Open an EFTS NetCDF file."""
    # raise NotImplemented("open_efts")
    # if isinstance(ncfile, str):
    #     nc = ncdf4::nc_open(ncfile, readunlim = FALSE, write = writein)
    # } else if (methods::is(ncfile, "ncdf4")) {
    #     nc = ncfile
    # }
    return EftsDataSet(ncfile)
```

## xr_efts

```
xr_efts(
    issue_times: Iterable[ConvertibleToTimestamp],
    station_ids: Iterable[str],
    lead_times: Optional[Iterable[int]] = None,
    lead_time_tstep: str = "hours",
    ensemble_size: int = 1,
    station_names: Optional[Iterable[str]] = None,
    latitudes: Optional[Iterable[float]] = None,
    longitudes: Optional[Iterable[float]] = None,
    areas: Optional[Iterable[float]] = None,
    nc_attributes: Optional[Dict[str, str]] = None,
) -> Dataset
```

Create an xarray Dataset for EFTS data.

Source code in `src/efts_io/wrapper.py`

```
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
```
