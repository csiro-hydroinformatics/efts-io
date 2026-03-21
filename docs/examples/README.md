# Examples

This directory contains example scripts demonstrating key features of `efts-io`.

## Running Examples

All examples can be run directly with Python:

```bash
python create_metadata_example.py
```

## Available Examples

### create_metadata_example.py

Demonstrates the improved API for creating metadata attributes that comply with STF 2.0 conventions.

**Key features shown:**
- Using type-safe enumerations (`TimeSeriesType`, `DataOriginType`, `LocationType`)
- Creating complete attributes with `create_variable_attributes()`
- Examples for different variable types (rainfall, streamflow, temperature, etc.)
- Integrating attributes with `EftsDataSet`
- Listing all available enumeration values

**Run it:**
```bash
python create_metadata_example.py
```

**Output:** The script prints formatted examples showing how to create attributes for various hydrological variables using the new type-safe API.

## See Also

- [Creating Metadata Attributes Tutorial](../creating_metadata_attributes.md)
- [STF 2.0 Conventions](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting/)
- [Basic Usage Notebook](../nb/basic_usage.ipynb)
