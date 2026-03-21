"""efts-io package.

Ensemble forecast time series
"""

from __future__ import annotations

# Metadata attribute creation (recommended API)
from efts_io.attributes import (
    DataOriginType,
    LocationType,
    TimeSeriesType,
    _create_template_variable_attributes,
    create_global_attributes,
    create_var_attribute_definition,
    create_variable_attributes,
)

# Main classes and functions
from efts_io.wrapper import EftsDataSet, create_efts, create_mandatory_global_attributes, open_efts, xr_efts

# import netCDF4

__all__: list[str] = [
    "DataOriginType",
    # Main classes
    "EftsDataSet",
    "LocationType",
    # Metadata enumerations
    "TimeSeriesType",
    # Dataset creation functions
    "create_efts",
    "create_global_attributes",
    "create_mandatory_global_attributes",
    "create_var_attribute_definition",
    # Attribute creation functions
    "create_variable_attributes",
    "open_efts",
    "_create_template_variable_attributes",
    "xr_efts",
]
