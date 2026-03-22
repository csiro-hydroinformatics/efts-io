# Creating Metadata Attributes for Variables

When working with `efts-io`, you need to provide metadata attributes for each data variable you create. These attributes must comply with the [STF 2.0 conventions](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting/).

## The Challenge

STF 2.0 conventions use numeric codes and string identifiers that can be cryptic:
- Type codes: `1` (instantaneous), `2` (accumulated), `3` (averaged), etc.
- Data origin codes: `"obs"`, `"der"`, `"sim"`, `"fct"`
- Location types: `"Point"`, `"Area"`

Remembering these codes and their meanings is error-prone.

## The Solution: Type-Safe Enumerations

`efts-io` provides enumeration classes that make attribute creation intuitive and type-safe:

```python
from efts_io.attributes import (
    TimeSeriesType,      # How data is aggregated
    DataOriginType,      # Where data comes from
    LocationType,        # Point or area measurement
    create_variable_attributes
)
```

## Approach 1: Create Complete Attributes (Recommended)

Use `create_variable_attributes()` to create all attributes in one call:

```python
from efts_io.attributes import (
    create_variable_attributes,
    TimeSeriesType,
    DataOriginType,
    LocationType
)

# Create attributes for observed rainfall (accumulated)
rain_attrs = create_variable_attributes(
    long_name="observed rainfall",
    units="mm",
    time_series_type=TimeSeriesType.ACCUMULATED,
    data_origin=DataOriginType.OBSERVED,
    data_description="gauge measurements from station network",
    location_type=LocationType.POINT,
    fill_value=-9999.0
)

# Create attributes for simulated streamflow (averaged)
flow_attrs = create_variable_attributes(
    long_name="simulated streamflow",
    units="m3/s",
    time_series_type=TimeSeriesType.AVERAGED,
    data_origin=DataOriginType.SIMULATED,
    data_description="GR4H model output forced with observed rainfall",
    location_type=LocationType.POINT
)

# Create attributes for forecast streamflow
forecast_attrs = create_variable_attributes(
    long_name="forecast streamflow",
    units="m3/s",
    time_series_type=TimeSeriesType.AVERAGED,
    data_origin=DataOriginType.FORECAST,
    data_description="GR4H model forecast forced with NWP rainfall",
    location_type=LocationType.POINT
)
```

## Approach 2: Start with a Template

If you prefer a step-by-step approach, use `template_variable_attributes()`:

```python
from efts_io import template_variable_attributes
from efts_io.attributes import TimeSeriesType, DataOriginType

# Get a blank template
attrs = template_variable_attributes()
attrs['long_name'] = "observed rainfall"
attrs['units'] = "mm"
attrs['type'] = 2  # Still need to know the code
attrs['type_description'] = "accumulated over the preceding interval"
attrs['dat_type'] = "obs"
# ... and so on

# OR get a partially pre-filled template (better!)
attrs = template_variable_attributes(
    time_series_type=TimeSeriesType.ACCUMULATED,
    data_origin=DataOriginType.OBSERVED
)
# Now type, type_description, dat_type are already filled
attrs['long_name'] = "observed rainfall"
attrs['units'] = "mm"
attrs['dat_type_description'] = "gauge measurements"
```

## Available Enumeration Values

### TimeSeriesType

```python
from efts_io.attributes import TimeSeriesType

# Common types for water forecasting
TimeSeriesType.INSTANTANEOUS          # Code: 1 - e.g., stage height
TimeSeriesType.ACCUMULATED            # Code: 2 - e.g., rainfall
TimeSeriesType.AVERAGED               # Code: 3 - e.g., flow, average temp
TimeSeriesType.ACCUMULATED_FORECAST   # Code: 4 - e.g., cumulative flow
TimeSeriesType.POINT_IN_INTERVAL      # Code: 5 - e.g., max/min temp

# Climatology variants (11-15)
TimeSeriesType.CLIMATOLOGY_INSTANTANEOUS
TimeSeriesType.CLIMATOLOGY_ACCUMULATED
# ... and so on
```

### DataOriginType

```python
from efts_io.attributes import DataOriginType

DataOriginType.OBSERVED   # Code: "obs" - direct observations
DataOriginType.DERIVED    # Code: "der" - derived from observations
DataOriginType.SIMULATED  # Code: "sim" - simulated from historical data
DataOriginType.FORECAST   # Code: "fct" - forecast from predictions
```

### LocationType

```python
from efts_io.attributes import LocationType

LocationType.POINT  # Point measurement (e.g., gauge)
LocationType.AREA   # Area-averaged (e.g., subcatchment)
```

## Using with EftsDataSet

```python
import numpy as np
from efts_io import xr_efts, EftsDataSet
from efts_io.attributes import (
    create_variable_attributes,
    TimeSeriesType,
    DataOriginType
)
import pandas as pd

# Create a dataset
times = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
station_ids = ["station_1", "station_2"]

dataset = xr_efts(
    issue_times=times,
    station_ids=station_ids,
    nc_attributes={
        "title": "Example dataset",
        "institution": "My Organization",
        "source": "Hydrological model",
        "catchment": "Test_Catchment",
        "comment": "Example data",
        "history": "Created for documentation"
    }
)

eds = EftsDataSet(dataset)

# Create variable with our new attributes
rain_attrs = create_variable_attributes(
    long_name="observed rainfall",
    units="mm",
    time_series_type=TimeSeriesType.ACCUMULATED,
    data_origin=DataOriginType.OBSERVED,
    data_description="gauge measurements"
)

eds.new_variable(
    varname="rain_obs",
    dim_names=["station_id", "time"],
    var_attributes=rain_attrs,
    data=np.random.rand(len(station_ids), len(times)) * 10
)

print(eds.data["rain_obs"].attrs)
```

## Benefits

1. **Type Safety**: Enums prevent typos and invalid codes
2. **Autocomplete**: IDEs can suggest valid options
3. **Self-Documenting**: Code is more readable
4. **Error Prevention**: Compiler catches invalid combinations
5. **Backwards Compatible**: Old API still works

## Migration Guide

If you have existing code using numeric codes:

```python
# Old way (still works but not recommended)
attrs = {
    'long_name': 'rainfall',
    'units': 'mm',
    '_FillValue': -9999.0,
    'type': 2,  # What does 2 mean?
    'type_description': 'accumulated over the preceding interval',
    'dat_type': 'obs',  # Easy to typo as "obd" or "obc"
    'dat_type_description': 'gauge data',
    'location_type': 'Point'
}

# New way (recommended)
from efts_io.attributes import create_variable_attributes, TimeSeriesType, DataOriginType

attrs = create_variable_attributes(
    long_name='rainfall',
    units='mm',
    time_series_type=TimeSeriesType.ACCUMULATED,  # Clear and explicit
    data_origin=DataOriginType.OBSERVED,           # No typos possible
    data_description='gauge data'
)
```

## See Also

- [STF 2.0 Conventions](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting/)
- [API Reference](../reference/api.md)
- [Basic Usage Tutorial](nb/basic_usage.ipynb)

## Quality Code Variable Attributes

Quality code variables (e.g., `rain_obs_qul`, `q_sim_qul`) have distinct attributes from data variables. Use `create_quality_variable_attributes()`:

```python
from efts_io.attributes import create_quality_variable_attributes

attrs = create_quality_variable_attributes(
    long_name="Quality of observed rainfall",
    quality_code_standard="ABC Quality coding",
)
# Result: {'long_name': 'Quality of observed rainfall', 'units': 'ABC Quality coding', '_FillValue': -1}
```

Key differences from data variables:

- `units` holds the quality code standard name, not physical units
- `_FillValue` is an **integer** (default: -1), not a float

## State Variable Attributes

State variables (`sv1`, `sv2`, ...) store internal model states. Use `create_state_variable_attributes()`:

```python
from efts_io.attributes import create_state_variable_attributes

attrs = create_state_variable_attributes(
    long_name="state var 1",
    model_name="GR4H_RR",
    sv_name="UH_Inflow",
    sv_description="Total inflow to Unit Hydrographs in GR4H",
)
# Result: {'long_name': 'state var 1', 'model_name': 'GR4H_RR',
#          'sv_name': 'UH_Inflow', 'sv_description': '...', '_FillValue': -9999.0}
```

## Global Attributes

`create_global_attributes()` now produces all 8 STF 2.0 required global attributes:

```python
from efts_io.attributes import create_global_attributes

attrs = create_global_attributes(
    title="Rainfall forecasts generated by ACCESS",
    institution="CSIRO Land & Water",
    source="https://example.com/data-reference",
    catchment="South_Esk",
    comment="Example dataset",
)
# Includes STF_convention_version=2.0, STF_nc_spec=<URL>, history=""
```

The three new keys (`STF_convention_version`, `STF_nc_spec`, `history`) have sensible defaults, so existing code continues to work unchanged.

## Attribute Validation

Validate attribute dictionaries before writing to file using the `validate_*` functions. Each returns a list of error strings (empty = valid):

```python
from efts_io.attributes import (
    create_variable_attributes,
    create_quality_variable_attributes,
    create_global_attributes,
    validate_variable_attributes,
    validate_quality_variable_attributes,
    validate_state_variable_attributes,
    validate_global_attributes,
    TimeSeriesType,
    DataOriginType,
)

# Validate data variable attributes
attrs = create_variable_attributes(
    long_name="observed rainfall",
    units="mm",
    time_series_type=TimeSeriesType.ACCUMULATED,
    data_origin=DataOriginType.OBSERVED,
    data_description="gauge measurements",
)
errors = validate_variable_attributes(attrs)
assert errors == []  # No errors

# Catch mistakes in hand-built dicts
bad_attrs = {"long_name": "test", "type": 99}  # missing keys, invalid type code
errors = validate_variable_attributes(bad_attrs)
# errors: ['Missing required attribute ...', "Attribute 'type' has value 99, ..."]

# Validate quality variable attributes
qul_attrs = create_quality_variable_attributes("Quality of observed rainfall", "ABC Quality coding")
errors = validate_quality_variable_attributes(qul_attrs)
assert errors == []

# Validate global attributes
global_attrs = create_global_attributes("Title", "Inst", "Src", "Catch", "Comment")
errors = validate_global_attributes(global_attrs)
assert errors == []
```

Available validators:

| Function | Checks |
|---|---|
| `validate_variable_attributes()` | 8 required keys, valid type codes (1-5, 11-15), valid dat_type codes, valid location_type |
| `validate_quality_variable_attributes()` | 3 required keys, `_FillValue` is int |
| `validate_state_variable_attributes()` | 5 required keys, `_FillValue` is numeric |
| `validate_global_attributes()` | 8 required keys, `STF_convention_version` is numeric, `title` non-empty |
