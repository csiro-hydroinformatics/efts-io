"""Management of netCDF attributes.

This module provides user-friendly classes and functions for creating
STF 2.0 compliant metadata attributes for netCDF variables.
"""

from typing import Any, Optional

from efts_io.conventions import (
    CATCHMENT_ATTR_KEY,
    COMMENT_ATTR_KEY,
    DAT_TYPE_ATTR_KEY,
    DAT_TYPE_DESCRIPTION_ATTR_KEY,
    FILLVALUE_ATTR_KEY,
    HISTORY_ATTR_KEY,
    INSTITUTION_ATTR_KEY,
    LOCATION_TYPE_ATTR_KEY,
    LONG_NAME_ATTR_KEY,
    MODEL_NAME_ATTR_KEY,
    SOURCE_ATTR_KEY,
    STF_2_0_URL,
    STF_CONVENTION_VERSION_ATTR_KEY,
    STF_NC_SPEC_ATTR_KEY,
    SV_DESCRIPTION_ATTR_KEY,
    SV_NAME_ATTR_KEY,
    TITLE_ATTR_KEY,
    TYPE_ATTR_KEY,
    TYPE_DESCRIPTION_ATTR_KEY,
    UNITS_ATTR_KEY,
    DataOriginType,
    LocationType,
    TimeSeriesType,
)


def create_var_attribute_definition(
    data_type_code: int = 2,
    type_description: str = "accumulated over the preceding interval",
    dat_type: str = "der",
    dat_type_description: str = "AWAP data interpolated from observations",
    location_type: str = "Point",
) -> dict[str, str]:
    """Create variable attribute definition (legacy function).

    .. deprecated::
        This function is maintained for backward compatibility.
        For new code, use :func:`create_variable_attributes` with the type-safe enumerations
        (:class:`TimeSeriesType`, :class:`DataOriginType`, :class:`LocationType`) instead.

    Args:
        data_type_code: Numeric code for time series type (1-5, 11-15)
        type_description: Description of the aggregation type
        dat_type: String code for data origin ("obs", "der", "sim", "fct")
        dat_type_description: Description of the data
        location_type: "Point" or "Area"

    Returns:
        Dictionary of type-related attributes

    Examples:
        >>> # Old way (still works but not recommended)
        >>> attrs = create_var_attribute_definition(
        ...     data_type_code=2,
        ...     type_description="accumulated over the preceding interval",
        ...     dat_type="obs",
        ... )
        >>>
        >>> # New recommended way
        >>> from efts_io.attributes import (
        ...     create_variable_attributes,
        ...     TimeSeriesType,
        ...     DataOriginType,
        ... )
        >>> attrs = create_variable_attributes(
        ...     long_name="observed rainfall",
        ...     units="mm",
        ...     time_series_type=TimeSeriesType.ACCUMULATED,
        ...     data_origin=DataOriginType.OBSERVED,
        ...     data_description="gauge measurements",
        ... )
    """
    return {
        TYPE_ATTR_KEY: str(data_type_code),
        TYPE_DESCRIPTION_ATTR_KEY: type_description,
        DAT_TYPE_ATTR_KEY: dat_type,
        DAT_TYPE_DESCRIPTION_ATTR_KEY: dat_type_description,
        LOCATION_TYPE_ATTR_KEY: location_type,
    }


def create_variable_attributes(
    long_name: str,
    units: str,
    time_series_type: TimeSeriesType,
    data_origin: DataOriginType,
    data_description: str,
    location_type: LocationType = LocationType.POINT,
    fill_value: float = -9999.0,
) -> dict[str, Any]:
    """Create variable attributes for STF 2.0 compliant netCDF files.

    This is the recommended function for creating metadata attributes for data variables.
    It uses type-safe enumerations to ensure attributes conform to STF 2.0 conventions
    without requiring users to remember numeric codes or string identifiers.

    Args:
        long_name: Human-readable name for the variable (e.g., "observed rainfall")
        units: Units of measurement (e.g., "mm", "m3/s", "°C")
        time_series_type: How the data is aggregated/sampled (use TimeSeriesType enum)
        data_origin: How the data was obtained (use DataOriginType enum)
        data_description: Detailed description of the data (e.g., "AWAP data interpolated from observations")
        location_type: Whether data is point or area measurement (default: POINT)
        fill_value: Value used for missing data (default: -9999.0)

    Returns:
        Dictionary of attributes ready to use with xarray DataArray or EftsDataSet.new_variable()

    Examples:
        >>> from efts_io.attributes import (
        ...     create_variable_attributes,
        ...     TimeSeriesType,
        ...     DataOriginType,
        ...     LocationType,
        ... )
        >>> attrs = create_variable_attributes(
        ...     long_name="observed rainfall",
        ...     units="mm",
        ...     time_series_type=TimeSeriesType.ACCUMULATED,
        ...     data_origin=DataOriginType.OBSERVED,
        ...     data_description="gauge measurements from station network",
        ...     location_type=LocationType.POINT,
        ... )
        >>> attrs["type"]
        2
        >>> attrs["type_description"]
        'accumulated over the preceding interval'
        >>> attrs["dat_type"]
        'obs'

    See Also:
        - TimeSeriesType: Enumeration of valid time series aggregation types
        - DataOriginType: Enumeration of valid data origin types
        - LocationType: Enumeration of valid location types
        - template_variable_attributes: For getting an empty template dictionary
    """
    return {
        LONG_NAME_ATTR_KEY: long_name,
        UNITS_ATTR_KEY: units,
        FILLVALUE_ATTR_KEY: fill_value,
        TYPE_ATTR_KEY: time_series_type.code,
        TYPE_DESCRIPTION_ATTR_KEY: time_series_type.description,
        DAT_TYPE_ATTR_KEY: data_origin.code,
        DAT_TYPE_DESCRIPTION_ATTR_KEY: data_description,
        LOCATION_TYPE_ATTR_KEY: location_type.value,
    }


def template_variable_attributes(
    time_series_type: Optional["TimeSeriesType"] = None,
    data_origin: Optional["DataOriginType"] = None,
    location_type: Optional["LocationType"] = None,
    fill_value: float = -9999.0,
) -> dict[str, Any]:
    """Create a template dictionary for variable attributes.

    This function provides a starting point for creating variable attributes
    that comply with STF 2.0 conventions. For the recommended type-safe approach,
    use the enumerations from efts_io.attributes.

    Args:
        time_series_type: TimeSeriesType enum or None (pre-fills type info if provided)
        data_origin: DataOriginType enum or None (pre-fills data origin if provided)
        location_type: LocationType enum or None (defaults to POINT)
        fill_value: Value for missing data (default: -9999.0)

    Returns:
        Dictionary with all required attribute keys

    Examples:
        >>> from efts_io import EftsDataSet
        >>> from efts_io.attributes import TimeSeriesType, DataOriginType
        >>>
        >>> # Using type-safe enums (recommended)
        >>> attrs = template_variable_attributes(
        ...     time_series_type=TimeSeriesType.ACCUMULATED,
        ...     data_origin=DataOriginType.OBSERVED,
        ... )
        >>> attrs["long_name"] = "observed rainfall"
        >>> attrs["units"] = "mm"
        >>>
        >>> # Or get a blank template
        >>> attrs = template_variable_attributes()

    Note:
        For complete attribute creation in one call, use:
        `from efts_io.attributes import create_variable_attributes`

    See Also:
        - efts_io.attributes.create_variable_attributes: Type-safe attribute creation
        - efts_io.attributes.TimeSeriesType: Valid time series aggregation types
        - efts_io.attributes.DataOriginType: Valid data origin types
        - efts_io.attributes.LocationType: Valid location types
    """
    from efts_io.attributes import LocationType

    if location_type is None:
        location_type = LocationType.POINT

    return _create_template_variable_attributes(
        time_series_type=time_series_type,
        data_origin=data_origin,
        location_type=location_type,
        fill_value=fill_value,
    )


def _create_template_variable_attributes(
    time_series_type: TimeSeriesType | None = None,
    data_origin: DataOriginType | None = None,
    location_type: LocationType = LocationType.POINT,
    fill_value: float = -9999.0,
) -> dict[str, Any]:
    """Create a template dictionary for variable attributes with optional pre-filled values.

    This function provides a starting point for creating variable attributes.
    You can specify the type information upfront, then fill in the remaining fields.

    Args:
        time_series_type: Optional TimeSeriesType to pre-fill (default: None, leaves empty)
        data_origin: Optional DataOriginType to pre-fill (default: None, leaves empty)
        location_type: LocationType to use (default: POINT)
        fill_value: Value for missing data (default: -9999.0)

    Returns:
        Dictionary with all required attribute keys, some pre-filled based on arguments

    Examples:
        >>> from efts_io.attributes import (
        ...     template_variable_attributes,
        ...     TimeSeriesType,
        ...     DataOriginType,
        ... )
        >>>
        >>> # Get a blank template
        >>> attrs = template_variable_attributes()
        >>> attrs["long_name"] = "my variable"
        >>> attrs["units"] = "mm"
        >>>
        >>> # Get a partially filled template
        >>> attrs = template_variable_attributes(
        ...     time_series_type=TimeSeriesType.ACCUMULATED,
        ...     data_origin=DataOriginType.OBSERVED,
        ... )
        >>> attrs["type"]
        2
        >>> attrs["long_name"] = "observed rainfall"
        >>> attrs["units"] = "mm"

    See Also:
        - create_variable_attributes: For creating complete attributes in one call
        - TimeSeriesType: Enumeration of valid time series types
        - DataOriginType: Enumeration of valid data origin types
    """
    if time_series_type is not None and data_origin is not None:
        return {
            LONG_NAME_ATTR_KEY: "",
            UNITS_ATTR_KEY: "",
            FILLVALUE_ATTR_KEY: fill_value,
            TYPE_ATTR_KEY: time_series_type.code,
            TYPE_DESCRIPTION_ATTR_KEY: time_series_type.description,
            DAT_TYPE_ATTR_KEY: data_origin.code,
            DAT_TYPE_DESCRIPTION_ATTR_KEY: "",
            LOCATION_TYPE_ATTR_KEY: location_type.value,
        }
    if time_series_type is not None:
        return {
            LONG_NAME_ATTR_KEY: "",
            UNITS_ATTR_KEY: "",
            FILLVALUE_ATTR_KEY: fill_value,
            TYPE_ATTR_KEY: time_series_type.code,
            TYPE_DESCRIPTION_ATTR_KEY: time_series_type.description,
            DAT_TYPE_ATTR_KEY: "",
            DAT_TYPE_DESCRIPTION_ATTR_KEY: "",
            LOCATION_TYPE_ATTR_KEY: location_type.value,
        }
    if data_origin is not None:
        return {
            LONG_NAME_ATTR_KEY: "",
            UNITS_ATTR_KEY: "",
            FILLVALUE_ATTR_KEY: fill_value,
            TYPE_ATTR_KEY: 0,
            TYPE_DESCRIPTION_ATTR_KEY: "",
            DAT_TYPE_ATTR_KEY: data_origin.code,
            DAT_TYPE_DESCRIPTION_ATTR_KEY: "",
            LOCATION_TYPE_ATTR_KEY: location_type.value,
        }
    # Return a completely blank template
    return {
        LONG_NAME_ATTR_KEY: "",
        UNITS_ATTR_KEY: "",
        FILLVALUE_ATTR_KEY: fill_value,
        TYPE_ATTR_KEY: 0,
        TYPE_DESCRIPTION_ATTR_KEY: "",
        DAT_TYPE_ATTR_KEY: "",
        DAT_TYPE_DESCRIPTION_ATTR_KEY: "",
        LOCATION_TYPE_ATTR_KEY: location_type.value,
    }


# # The following cannot be hard-coded.  ncdf4::ncatt_put(nc,0,'institution',
# # 'CSIRO Land and Water') ncdf4::ncatt_put(nc,0,'comment', '')
# # ncdf4::ncatt_put(nc,0,'source', '') catchment = paste(letters[1:9],
# # collapse='') ncdf4::ncatt_put(nc,0,'Catchment', catchment)
# # ncdf4::ncatt_put(nc,0,'title', paste('Rainfall Observations for',
# # catchment))

# #' Add a value to a global attribute of a netCDF file
# #'
# #' Add a value to a global attribute of a netCDF file
# #'
# #' @param nc an object 'ncdf4'
# #' @param attribute_name the name of the global attribute to add to
# #' @param attribute_value the value to pad
# #' @param sep separator to add between the existing value and the padded value.
# #' @export
# #' @import ncdf4
# pad_global_attribute(nc, attribute_name, attribute_value, sep = "\n") {
#   attVal = ""
#   a = ncdf4::ncatt_get(nc, 0, attribute_name)
#   if (a$hasatt) {
#     attVal = paste(a$value, sep)
#     attVal = paste(attVal, attribute_value)
#   } else {
#     attVal = attribute_value
#   }
#   ncdf4::ncatt_put(nc, 0, attribute_name, as.character(attVal))
# }


#' Define a set of global attributes for netCDF files.
#'
#' The conventions require a set of global attributes to be present,
#' see \url{https://github.com/jmp75/efts/blob/master/docs/netcdf_for_water_forecasting.md#global-attributes}.
#' This function is recommended to define these attributes.
#'
#' @param title text, a succinct description of what is in the dataset
#' @param institution text, Where the original data was produced
#' @param source text, published or web-based references that describe the data or methods used to produce it
#' @param catchment text, the catchment for which the data is created. White spaces are replaced with underscores
#' @param comment text, miscellaneous information
#' @param strict logical, if true perform extra checks on the input information
#' @export
#' @importFrom stringr str_replace_all
def create_global_attributes(
    title: str,
    institution: str,
    source: str,
    catchment: str,
    comment: str,
    stf_convention_version: float = 2.0,
    stf_nc_spec: str = STF_2_0_URL,
    history: str = "",
) -> dict[str, Any]:
    """Creates STF global attributes.

    Args:
        title (str): title
        institution (str): institution
        source (str): source
        catchment (str): catchment
        comment (str): comment
        stf_convention_version (float): STF convention version (default: 2.0)
        stf_nc_spec (str): URL to the STF specification document (default: STF 2.0 URL)
        history (str): audit trail for modifications to the original data (default: "")

    Raises:
        ValueError: Unexpected or insufficient information

    Returns:
        dict[str, Any]: dictionary of global attributes
    """
    # catchment info should not have white spaces (and why was that???)
    # catchment = 'Upper  Murray River '
    # catchment = stringr::str_replace_all(catchment, pattern='\\s+', '_')

    if title == "":
        raise ValueError("Empty title is not accepted as a valid attribute")

    return {
        TITLE_ATTR_KEY: title,
        INSTITUTION_ATTR_KEY: institution,
        SOURCE_ATTR_KEY: source,
        CATCHMENT_ATTR_KEY: catchment,
        STF_CONVENTION_VERSION_ATTR_KEY: stf_convention_version,
        STF_NC_SPEC_ATTR_KEY: stf_nc_spec,
        COMMENT_ATTR_KEY: comment,
        HISTORY_ATTR_KEY: history,
    }


# ########################################
# # Below are functions not exported
# ########################################

# check_global_attributes(nc_attributes)
# {
#   stopifnot(is.list(nc_attributes))
#   expected = mandatory_global_attributes
#   present_attr = expected %in% names(nc_attributes)
#   missing_attr = which(!present_attr)
#   if(length(missing_attr) > 0) stop(paste("missing global attributes: ",paste(expected[missing_attr], collapse=","), sep=" "))
# }

# put_variable_attributes(data_var_def, nc) {
#   a = data_var_def
#   stopifnot("name" %in% names(a))
#   varname = a[["name"]]
#   if ("attributes" %in% names(a)) {
#     attribs = a[["attributes"]]
#     for (attribute_name in names(attribs)) {
#       ncdf4::ncatt_put(nc, varname, attribute_name, attribs[[attribute_name]])
#     }
#   }
# }


def create_quality_variable_attributes(
    long_name: str,
    quality_code_standard: str,
    fill_value: int = -1,
) -> dict[str, Any]:
    """Create attributes for a quality code variable (e.g., rain_obs_qual).

    Quality code variables have a distinct set of attributes from data variables.
    Per the STF 2.0 conventions, they require ``long_name``, ``units`` (the quality
    code standard), and ``_FillValue`` (an integer, default -1).

    Args:
        long_name: Human-readable name (e.g., "Quality of observed rainfall")
        quality_code_standard: Quality code standard used (e.g., "ABC Quality coding")
        fill_value: Integer fill value for missing data (default: -1)

    Returns:
        Dictionary of attributes ready to use with xarray DataArray or EftsDataSet.new_variable()

    Examples:
        >>> attrs = create_quality_variable_attributes(
        ...     long_name="Quality of observed rainfall",
        ...     quality_code_standard="ABC Quality coding",
        ... )
        >>> attrs["_FillValue"]
        -1
    """
    return {
        LONG_NAME_ATTR_KEY: long_name,
        UNITS_ATTR_KEY: quality_code_standard,
        FILLVALUE_ATTR_KEY: fill_value,
    }


def create_state_variable_attributes(
    long_name: str,
    model_name: str,
    sv_name: str,
    sv_description: str,
    fill_value: float = -9999.0,
) -> dict[str, Any]:
    """Create attributes for a state variable (e.g., sv1, sv2).

    State variables store internal model states. Per the STF 2.0 conventions,
    they require ``long_name``, ``model_name``, ``sv_name``, ``sv_description``,
    and ``_FillValue``.

    Args:
        long_name: Human-readable name (e.g., "state var 1")
        model_name: Name of the model (e.g., "GR4H_RR")
        sv_name: Name of the state variable in the model (e.g., "UH_Inflow")
        sv_description: Description of the state variable (e.g., "Total inflow to Unit Hydrographs in GR4H")
        fill_value: Fill value for missing data (default: -9999.0)

    Returns:
        Dictionary of attributes ready to use with xarray DataArray or EftsDataSet.new_variable()

    Examples:
        >>> attrs = create_state_variable_attributes(
        ...     long_name="state var 1",
        ...     model_name="GR4H_RR",
        ...     sv_name="UH_Inflow",
        ...     sv_description="Total inflow to Unit Hydrographs in GR4H",
        ... )
        >>> attrs["model_name"]
        'GR4H_RR'
    """
    return {
        LONG_NAME_ATTR_KEY: long_name,
        MODEL_NAME_ATTR_KEY: model_name,
        SV_NAME_ATTR_KEY: sv_name,
        SV_DESCRIPTION_ATTR_KEY: sv_description,
        FILLVALUE_ATTR_KEY: fill_value,
    }


# ===================================================================
# Attribute validation functions
# ===================================================================

_VALID_TYPE_CODES = {1, 2, 3, 4, 5, 11, 12, 13, 14, 15}
_VALID_DAT_TYPE_CODES = {"obs", "der", "sim", "fct"}
_VALID_LOCATION_TYPES = {"Point", "Area"}


def validate_variable_attributes(attrs: dict[str, Any]) -> list[str]:
    """Validate a dictionary of data variable attributes against STF 2.0 conventions.

    Checks that all required keys are present and that coded values are valid.

    Args:
        attrs: Dictionary of attributes to validate

    Returns:
        List of error message strings. Empty list means valid.

    Examples:
        >>> errors = validate_variable_attributes({})
        >>> len(errors) > 0
        True
    """
    errors: list[str] = []
    required_keys = {
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: (int, float),
        TYPE_ATTR_KEY: int,
        TYPE_DESCRIPTION_ATTR_KEY: str,
        DAT_TYPE_ATTR_KEY: str,
        DAT_TYPE_DESCRIPTION_ATTR_KEY: str,
        LOCATION_TYPE_ATTR_KEY: str,
    }

    for key, expected_type in required_keys.items():
        if key not in attrs:
            errors.append(f"Missing required attribute '{key}'")
        elif not isinstance(attrs[key], expected_type):
            errors.append(
                f"Attribute '{key}' has type '{type(attrs[key]).__name__}',"
                f" expected '{expected_type.__name__ if isinstance(expected_type, type) else ' or '.join(t.__name__ for t in expected_type)}'",
            )

    if (
        TYPE_ATTR_KEY in attrs
        and isinstance(attrs[TYPE_ATTR_KEY], int)
        and attrs[TYPE_ATTR_KEY] not in _VALID_TYPE_CODES
    ):
        errors.append(
            f"Attribute '{TYPE_ATTR_KEY}' has value {attrs[TYPE_ATTR_KEY]},"
            f" expected one of {sorted(_VALID_TYPE_CODES)}",
        )

    if (
        DAT_TYPE_ATTR_KEY in attrs
        and isinstance(attrs[DAT_TYPE_ATTR_KEY], str)
        and attrs[DAT_TYPE_ATTR_KEY] not in _VALID_DAT_TYPE_CODES
    ):
        errors.append(
            f"Attribute '{DAT_TYPE_ATTR_KEY}' has value '{attrs[DAT_TYPE_ATTR_KEY]}',"
            f" expected one of {sorted(_VALID_DAT_TYPE_CODES)}",
        )

    if (
        LOCATION_TYPE_ATTR_KEY in attrs
        and isinstance(attrs[LOCATION_TYPE_ATTR_KEY], str)
        and attrs[LOCATION_TYPE_ATTR_KEY] not in _VALID_LOCATION_TYPES
    ):
        errors.append(
            f"Attribute '{LOCATION_TYPE_ATTR_KEY}' has value '{attrs[LOCATION_TYPE_ATTR_KEY]}',"
            f" expected one of {sorted(_VALID_LOCATION_TYPES)}",
        )

    return errors


def validate_quality_variable_attributes(attrs: dict[str, Any]) -> list[str]:
    """Validate a dictionary of quality variable attributes against STF 2.0 conventions.

    Args:
        attrs: Dictionary of attributes to validate

    Returns:
        List of error message strings. Empty list means valid.

    Examples:
        >>> from efts_io.attributes import create_quality_variable_attributes
        >>> attrs = create_quality_variable_attributes(
        ...     "Quality of observed rainfall", "ABC Quality coding"
        ... )
        >>> validate_quality_variable_attributes(attrs)
        []
    """
    errors: list[str] = []
    required_keys = {
        LONG_NAME_ATTR_KEY: str,
        UNITS_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: int,
    }

    for key, expected_type in required_keys.items():
        if key not in attrs:
            errors.append(f"Missing required attribute '{key}'")
        elif not isinstance(attrs[key], expected_type):
            errors.append(
                f"Attribute '{key}' has type '{type(attrs[key]).__name__}', expected '{expected_type.__name__}'",
            )

    return errors


def validate_state_variable_attributes(attrs: dict[str, Any]) -> list[str]:
    """Validate a dictionary of state variable attributes against STF 2.0 conventions.

    Args:
        attrs: Dictionary of attributes to validate

    Returns:
        List of error message strings. Empty list means valid.

    Examples:
        >>> from efts_io.attributes import create_state_variable_attributes
        >>> attrs = create_state_variable_attributes("sv1", "GR4H_RR", "UH_Inflow", "desc")
        >>> validate_state_variable_attributes(attrs)
        []
    """
    errors: list[str] = []
    required_keys = {
        LONG_NAME_ATTR_KEY: str,
        MODEL_NAME_ATTR_KEY: str,
        SV_NAME_ATTR_KEY: str,
        SV_DESCRIPTION_ATTR_KEY: str,
        FILLVALUE_ATTR_KEY: (int, float),
    }

    for key, expected_type in required_keys.items():
        if key not in attrs:
            errors.append(f"Missing required attribute '{key}'")
        elif not isinstance(attrs[key], expected_type):
            errors.append(
                f"Attribute '{key}' has type '{type(attrs[key]).__name__}',"
                f" expected '{expected_type.__name__ if isinstance(expected_type, type) else ' or '.join(t.__name__ for t in expected_type)}'",
            )

    return errors


def validate_global_attributes(attrs: dict[str, Any]) -> list[str]:
    """Validate a dictionary of global attributes against STF 2.0 conventions.

    Args:
        attrs: Dictionary of attributes to validate

    Returns:
        List of error message strings. Empty list means valid.

    Examples:
        >>> from efts_io.attributes import create_global_attributes
        >>> attrs = create_global_attributes("Title", "Inst", "Src", "Catch", "Comment")
        >>> validate_global_attributes(attrs)
        []
    """
    errors: list[str] = []
    required_keys = {
        TITLE_ATTR_KEY: str,
        INSTITUTION_ATTR_KEY: str,
        SOURCE_ATTR_KEY: str,
        CATCHMENT_ATTR_KEY: str,
        STF_CONVENTION_VERSION_ATTR_KEY: (int, float),
        STF_NC_SPEC_ATTR_KEY: str,
        COMMENT_ATTR_KEY: str,
        HISTORY_ATTR_KEY: str,
    }

    for key, expected_type in required_keys.items():
        if key not in attrs:
            errors.append(f"Missing required attribute '{key}'")
        elif not isinstance(attrs[key], expected_type):
            errors.append(
                f"Attribute '{key}' has type '{type(attrs[key]).__name__}',"
                f" expected '{expected_type.__name__ if isinstance(expected_type, type) else ' or '.join(t.__name__ for t in expected_type)}'",
            )

    if TITLE_ATTR_KEY in attrs and isinstance(attrs[TITLE_ATTR_KEY], str) and attrs[TITLE_ATTR_KEY] == "":
        errors.append(f"Attribute '{TITLE_ATTR_KEY}' must not be empty")

    if CATCHMENT_ATTR_KEY in attrs and isinstance(attrs[CATCHMENT_ATTR_KEY], str) and " " in attrs[CATCHMENT_ATTR_KEY]:
        errors.append(f"Attribute '{CATCHMENT_ATTR_KEY}' must not contain spaces (use underscores instead)")

    return errors
