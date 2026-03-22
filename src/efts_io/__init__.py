"""efts-io package.

Ensemble forecast time series
"""

from __future__ import annotations

# Metadata attribute creation (recommended API)
from efts_io.attributes import (
    DataOriginType,
    LocationType,
    TimeSeriesType,
    create_global_attributes,
    create_quality_variable_attributes,
    create_state_variable_attributes,
    create_var_attribute_definition,
    create_variable_attributes,
    template_variable_attributes,
    validate_global_attributes,
    validate_quality_variable_attributes,
    validate_state_variable_attributes,
    validate_variable_attributes,
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
    "create_quality_variable_attributes",
    "create_state_variable_attributes",
    "create_var_attribute_definition",
    # Attribute creation functions
    "create_variable_attributes",
    "open_efts",
    "template_variable_attributes",
    # Attribute validation functions
    "validate_global_attributes",
    "validate_quality_variable_attributes",
    "validate_state_variable_attributes",
    "validate_variable_attributes",
    "xr_efts",
]
