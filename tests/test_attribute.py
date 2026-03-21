"""Convention-driven tests for attribute creation functions.

Tests are derived from the STF 2.0 conventions specification
(https://github.com/csiro-hydroinformatics/efts-io/blob/42ee35f0f019e9bad48b94914429476a7e8278dc/docs/netcdf_for_water_forecasting.md),
not from the implementation.
"""

import pytest

from efts_io.attributes import (
    create_variable_attributes,
    template_variable_attributes,
)
from efts_io.conventions import (
    DataOriginType,
    LocationType,
    TimeSeriesType,
)


# ---------------------------------------------------------------------------
# Convention-defined expected values (from the STF 2.0 spec tables)
# ---------------------------------------------------------------------------

# "Description of time types" table in the conventions document
EXPECTED_TIME_SERIES_TYPES = {
    1: "instantaneous data",
    2: "accumulated over the preceding interval",
    3: "averaged over the preceding interval",
    4: "accumulated since start of forecast",
    5: "point value recorded in the preceding interval",
    11: "climatology data - instantaneous data",
    12: "climatology data - accumulated over the preceding interval",
    13: "climatology data - averaged over the preceding interval",
    14: "climatology data - accumulated since start of forecast",
    15: "climatology data - point value recorded in the preceding interval",
}

# "Description of data types" table in the conventions document
EXPECTED_DATA_ORIGIN_TYPES = {
    "obs": "observed directly",
    "der": "derived from observations",
    "sim": "simulated from observations",
    "fct": "simulated from forecasts",
}

# Convention-required attribute keys for data variables (from the variable attributes table)
REQUIRED_VARIABLE_ATTR_KEYS = {
    "long_name",
    "units",
    "_FillValue",
    "type",
    "type_description",
    "dat_type",
    "dat_type_description",
    "location_type",
}


# ===================================================================
# Phase 4: Cross-cutting convention compliance — enum exhaustiveness
# ===================================================================


class TestEnumConventionCoverage:
    """Verify the enumerations exhaustively cover the STF 2.0 conventions tables."""

    def test_time_series_type_has_exactly_10_members(self):
        assert len(TimeSeriesType) == 10

    def test_time_series_type_codes_match_conventions(self):
        actual_codes = {member.code for member in TimeSeriesType}
        assert actual_codes == set(EXPECTED_TIME_SERIES_TYPES.keys())

    @pytest.mark.parametrize(
        ("code", "expected_description"),
        list(EXPECTED_TIME_SERIES_TYPES.items()),
        ids=[f"type_{code}" for code in EXPECTED_TIME_SERIES_TYPES],
    )
    def test_time_series_type_descriptions_match_conventions(self, code, expected_description):
        matching = [m for m in TimeSeriesType if m.code == code]
        assert len(matching) == 1, f"Expected exactly one member with code {code}"
        assert matching[0].description == expected_description

    def test_data_origin_type_has_exactly_4_members(self):
        assert len(DataOriginType) == 4

    def test_data_origin_type_codes_match_conventions(self):
        actual_codes = {member.code for member in DataOriginType}
        assert actual_codes == set(EXPECTED_DATA_ORIGIN_TYPES.keys())

    @pytest.mark.parametrize(
        ("code", "expected_description"),
        list(EXPECTED_DATA_ORIGIN_TYPES.items()),
        ids=[f"dat_{code}" for code in EXPECTED_DATA_ORIGIN_TYPES],
    )
    def test_data_origin_type_descriptions_match_conventions(self, code, expected_description):
        matching = [m for m in DataOriginType if m.code == code]
        assert len(matching) == 1, f"Expected exactly one member with code {code}"
        assert matching[0].description == expected_description

    def test_location_type_has_exactly_2_members(self):
        assert len(LocationType) == 2

    def test_location_type_values_match_conventions(self):
        actual_values = {member.value for member in LocationType}
        assert actual_values == {"Point", "Area"}


# ===================================================================
# Phase 2: create_variable_attributes
# ===================================================================


class TestCreateVariableAttributes:
    """Tests for create_variable_attributes driven by STF 2.0 conventions."""

    def test_output_contains_all_required_attribute_keys(self):
        """The conventions require 8 specific attributes on data variables."""
        attrs = create_variable_attributes(
            long_name="observed rainfall",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
            data_description="gauge measurements",
        )
        assert set(attrs.keys()) == REQUIRED_VARIABLE_ATTR_KEYS

    def test_attribute_key_names_match_spec_exactly(self):
        """Key names must use exact STF 2.0 names: 'type' not 'type_code', 'dat_type' not 'data_type', etc."""
        attrs = create_variable_attributes(
            long_name="x",
            units="mm",
            time_series_type=TimeSeriesType.INSTANTANEOUS,
            data_origin=DataOriginType.OBSERVED,
            data_description="x",
        )
        # These exact strings come from the convention's attribute tables
        for key in ["long_name", "units", "_FillValue", "type", "type_description", "dat_type", "dat_type_description", "location_type"]:
            assert key in attrs, f"Missing convention-required key '{key}'"

    # -- Time series types (parametrized over all enum members) --

    @pytest.mark.parametrize(
        "ts_type",
        list(TimeSeriesType),
        ids=[m.name for m in TimeSeriesType],
    )
    def test_time_series_type_code_in_output(self, ts_type):
        """Convention: 'type' attribute is an int matching the time type code."""
        attrs = create_variable_attributes(
            long_name="test var",
            units="mm",
            time_series_type=ts_type,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
        )
        assert attrs["type"] == EXPECTED_TIME_SERIES_TYPES[ts_type.code] or attrs["type"] == ts_type.code
        # Specifically check the code
        assert attrs["type"] == ts_type.code

    @pytest.mark.parametrize(
        "ts_type",
        list(TimeSeriesType),
        ids=[m.name for m in TimeSeriesType],
    )
    def test_time_series_type_description_in_output(self, ts_type):
        """Convention: 'type_description' matches the description from the spec table."""
        attrs = create_variable_attributes(
            long_name="test var",
            units="mm",
            time_series_type=ts_type,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
        )
        expected = EXPECTED_TIME_SERIES_TYPES[ts_type.code]
        assert attrs["type_description"] == expected

    # -- Data origin types (parametrized over all enum members) --

    @pytest.mark.parametrize(
        "origin",
        list(DataOriginType),
        ids=[m.name for m in DataOriginType],
    )
    def test_data_origin_code_in_output(self, origin):
        """Convention: 'dat_type' is a string code from {"obs","der","sim","fct"}."""
        attrs = create_variable_attributes(
            long_name="test var",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=origin,
            data_description="test",
        )
        assert attrs["dat_type"] == origin.code
        assert attrs["dat_type"] in EXPECTED_DATA_ORIGIN_TYPES

    # -- Location type --

    def test_default_location_type_is_point(self):
        """Convention: default value of location_type is 'Point'."""
        attrs = create_variable_attributes(
            long_name="test",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
        )
        assert attrs["location_type"] == "Point"

    def test_location_type_area(self):
        """Convention: location_type can be 'Area' for areal data."""
        attrs = create_variable_attributes(
            long_name="areal rainfall",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.DERIVED,
            data_description="area-averaged",
            location_type=LocationType.AREA,
        )
        assert attrs["location_type"] == "Area"

    # -- Fill value --

    def test_default_fill_value(self):
        """Convention: _FillValue default is -9999f."""
        attrs = create_variable_attributes(
            long_name="test",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
        )
        assert attrs["_FillValue"] == -9999.0

    def test_custom_fill_value(self):
        attrs = create_variable_attributes(
            long_name="test",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
            fill_value=-1.0,
        )
        assert attrs["_FillValue"] == -1.0

    # -- Passthrough of user-provided strings --

    def test_long_name_stored_verbatim(self):
        attrs = create_variable_attributes(
            long_name="observed rainfall",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
            data_description="test",
        )
        assert attrs["long_name"] == "observed rainfall"

    def test_units_stored_verbatim(self):
        attrs = create_variable_attributes(
            long_name="test",
            units="m3/s",
            time_series_type=TimeSeriesType.AVERAGED,
            data_origin=DataOriginType.SIMULATED,
            data_description="test",
        )
        assert attrs["units"] == "m3/s"

    def test_data_description_stored_verbatim(self):
        desc = "AWAP data interpolated from observations"
        attrs = create_variable_attributes(
            long_name="test",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.DERIVED,
            data_description=desc,
        )
        assert attrs["dat_type_description"] == desc

    # -- Realistic convention scenarios --

    def test_observed_rainfall_scenario(self):
        """Convention example: observed rainfall (type=2, dat_type='der', units='mm', location='Point')."""
        attrs = create_variable_attributes(
            long_name="observed rainfall",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.DERIVED,
            data_description="AWAP data interpolated from observations",
        )
        assert attrs["type"] == 2
        assert attrs["type_description"] == "accumulated over the preceding interval"
        assert attrs["dat_type"] == "der"
        assert attrs["dat_type_description"] == "AWAP data interpolated from observations"
        assert attrs["location_type"] == "Point"
        assert attrs["units"] == "mm"
        assert attrs["_FillValue"] == -9999.0

    def test_simulated_streamflow_scenario(self):
        """Convention example: simulated streamflow (type=3, dat_type='sim', units='m3/s')."""
        attrs = create_variable_attributes(
            long_name="simulated streamflow",
            units="m3/s",
            time_series_type=TimeSeriesType.AVERAGED,
            data_origin=DataOriginType.SIMULATED,
            data_description="flow simulated by GR4H forced by observations",
        )
        assert attrs["type"] == 3
        assert attrs["type_description"] == "averaged over the preceding interval"
        assert attrs["dat_type"] == "sim"
        assert attrs["location_type"] == "Point"

    def test_forecast_streamflow_scenario(self):
        """Convention example: forecast streamflow (type=3, dat_type='fct')."""
        attrs = create_variable_attributes(
            long_name="forecast streamflow",
            units="m3/s",
            time_series_type=TimeSeriesType.AVERAGED,
            data_origin=DataOriginType.FORECAST,
            data_description="flow forecast by GR4H forced by NWP forecasts",
        )
        assert attrs["type"] == 3
        assert attrs["dat_type"] == "fct"

    def test_instantaneous_stage_height_scenario(self):
        """Convention example: instantaneous data such as stage height (type=1)."""
        attrs = create_variable_attributes(
            long_name="stage height",
            units="m",
            time_series_type=TimeSeriesType.INSTANTANEOUS,
            data_origin=DataOriginType.OBSERVED,
            data_description="gauge measurements",
        )
        assert attrs["type"] == 1
        assert attrs["type_description"] == "instantaneous data"
        assert attrs["dat_type"] == "obs"

    def test_minmax_temperature_scenario(self):
        """Convention example: min/max temperature (type=5, point value in interval)."""
        attrs = create_variable_attributes(
            long_name="maximum surface air temperature",
            units="°C",
            time_series_type=TimeSeriesType.POINT_IN_INTERVAL,
            data_origin=DataOriginType.OBSERVED,
            data_description="weather station measurements",
        )
        assert attrs["type"] == 5
        assert attrs["type_description"] == "point value recorded in the preceding interval"

    def test_area_averaged_rainfall_scenario(self):
        """Convention: location_type='Area' for subcatchment-averaged data."""
        attrs = create_variable_attributes(
            long_name="area-averaged rainfall",
            units="mm",
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.DERIVED,
            data_description="subcatchment-averaged AWAP rainfall",
            location_type=LocationType.AREA,
        )
        assert attrs["location_type"] == "Area"
        assert attrs["type"] == 2

    def test_accumulated_forecast_scenario(self):
        """Convention example: accumulated since start of forecast (type=4)."""
        attrs = create_variable_attributes(
            long_name="cumulative flow",
            units="m3",
            time_series_type=TimeSeriesType.ACCUMULATED_FORECAST,
            data_origin=DataOriginType.FORECAST,
            data_description="cumulative flow since forecast issue time",
        )
        assert attrs["type"] == 4
        assert attrs["type_description"] == "accumulated since start of forecast"
        assert attrs["dat_type"] == "fct"

    def test_climatology_rainfall_scenario(self):
        """Convention: climatology variant of accumulated data (type=12)."""
        attrs = create_variable_attributes(
            long_name="climatology rainfall",
            units="mm",
            time_series_type=TimeSeriesType.CLIMATOLOGY_ACCUMULATED,
            data_origin=DataOriginType.DERIVED,
            data_description="30-year climatology of accumulated rainfall",
        )
        assert attrs["type"] == 12
        assert attrs["type_description"] == "climatology data - accumulated over the preceding interval"


# ===================================================================
# Phase 3: template_variable_attributes
# ===================================================================


class TestTemplateVariableAttributes:
    """Tests for template_variable_attributes driven by STF 2.0 conventions."""

    def test_blank_template_has_all_required_keys(self):
        """A blank template must contain all convention-required attribute keys."""
        attrs = template_variable_attributes()
        assert set(attrs.keys()) == REQUIRED_VARIABLE_ATTR_KEYS

    def test_blank_template_defaults(self):
        """Blank template: empty strings for text, 0 for type code, -9999.0 for fill, 'Point' for location."""
        attrs = template_variable_attributes()
        assert attrs["long_name"] == ""
        assert attrs["units"] == ""
        assert attrs["_FillValue"] == -9999.0
        assert attrs["type"] == 0
        assert attrs["type_description"] == ""
        assert attrs["dat_type"] == ""
        assert attrs["dat_type_description"] == ""
        assert attrs["location_type"] == "Point"

    # -- Partial fills --

    @pytest.mark.parametrize(
        "ts_type",
        list(TimeSeriesType),
        ids=[m.name for m in TimeSeriesType],
    )
    def test_partial_fill_time_series_type_only(self, ts_type):
        """When only time_series_type is provided, type and type_description are pre-filled; dat_type is empty."""
        attrs = template_variable_attributes(time_series_type=ts_type)
        assert attrs["type"] == ts_type.code
        assert attrs["type_description"] == EXPECTED_TIME_SERIES_TYPES[ts_type.code]
        assert attrs["dat_type"] == ""

    @pytest.mark.parametrize(
        "origin",
        list(DataOriginType),
        ids=[m.name for m in DataOriginType],
    )
    def test_partial_fill_data_origin_only(self, origin):
        """When only data_origin is provided, dat_type is pre-filled; type is left as 0."""
        attrs = template_variable_attributes(data_origin=origin)
        assert attrs["dat_type"] == origin.code
        assert attrs["type"] == 0

    def test_partial_fill_both_enums(self):
        """When both enums are provided, both type and dat_type are pre-filled."""
        attrs = template_variable_attributes(
            time_series_type=TimeSeriesType.AVERAGED,
            data_origin=DataOriginType.SIMULATED,
        )
        assert attrs["type"] == 3
        assert attrs["type_description"] == "averaged over the preceding interval"
        assert attrs["dat_type"] == "sim"

    # -- Location type override --

    def test_custom_location_type_area(self):
        """Override default 'Point' with 'Area'."""
        attrs = template_variable_attributes(location_type=LocationType.AREA)
        assert attrs["location_type"] == "Area"

    def test_default_location_type_is_point(self):
        attrs = template_variable_attributes()
        assert attrs["location_type"] == "Point"

    # -- Custom fill value --

    def test_custom_fill_value(self):
        attrs = template_variable_attributes(fill_value=-1.0)
        assert attrs["_FillValue"] == -1.0

    # -- Workflow: template then fill in --

    def test_template_workflow_fill_then_verify(self):
        """Simulate the intended usage: get a template, fill blanks, and verify completeness."""
        attrs = template_variable_attributes(
            time_series_type=TimeSeriesType.ACCUMULATED,
            data_origin=DataOriginType.OBSERVED,
        )
        # User fills in the remaining fields
        attrs["long_name"] = "observed rainfall"
        attrs["units"] = "mm"
        attrs["dat_type_description"] = "gauge measurements from station network"

        # Now all keys should have meaningful (non-empty) values
        for key in REQUIRED_VARIABLE_ATTR_KEYS:
            assert key in attrs
            value = attrs[key]
            if isinstance(value, str):
                assert value != "", f"Attribute '{key}' should be filled in but is empty"
            elif isinstance(value, (int, float)):
                assert value != 0 or key == "type", f"Attribute '{key}' should be non-zero"

        # And the convention values should be correct
        assert attrs["type"] == 2
        assert attrs["dat_type"] == "obs"
        assert attrs["location_type"] == "Point"
        assert attrs["_FillValue"] == -9999.0
