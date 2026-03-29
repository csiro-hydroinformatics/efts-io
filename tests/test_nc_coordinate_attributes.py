"""Convention-driven tests for coordinate variable attributes in written NetCDF files.

Tests are derived from the STF 2.0 conventions specification
(https://github.com/csiro-hydroinformatics/efts-io/blob/42ee35f0f019e9bad48b94914429476a7e8278dc/docs/netcdf_for_water_forecasting.md),
not from the implementation.

Phase 1 — Coordinate variable attributes in written NetCDF
  Covers: time, ens_member, station_id, station_name, lat, lon, strLen.

Phase 2 — lead_time.units matches the timestep parameter
  Covers: lead_time standard_name, long_name, units (days and hours), axis.
  The convention §Description of Variables / lead_time requires units of the form
  "{timestep} since time" where timestep reflects the lead time step used.
  NB#1 in the spec: unit of lead_time does not have to equal unit of time, but both
  are passed via the same `timestep` argument to save_to_stf2 in the current API.
"""

import os
import platform
import tempfile

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytest

from efts_io._ncdf_stf2 import StfVariable
from efts_io.conventions import (
    AXIS_ATTR_KEY,
    ENS_MEMBER_DIMNAME,
    LAT_VARNAME,
    LEAD_TIME_DIMNAME,
    LONG_NAME_ATTR_KEY,
    LON_VARNAME,
    STANDARD_NAME_ATTR_KEY,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    STR_LEN_DIMNAME,
    TIME_DIMNAME,
    UNITS_ATTR_KEY,
    DataOriginType,
)
from efts_io.wrapper import EftsDataSet, xr_efts

# ---------------------------------------------------------------------------
# Convention-defined expected attribute values (from the STF 2.0 spec tables)
# ---------------------------------------------------------------------------

# §Description of Variables / time
EXPECTED_TIME_STANDARD_NAME = "time"
EXPECTED_TIME_LONG_NAME = "time"
EXPECTED_TIME_AXIS = "t"

# §Description of Variables / station_id
EXPECTED_STATION_ID_LONG_NAME = "station or node identification code"

# §Description of Variables / station_name
EXPECTED_STATION_NAME_LONG_NAME = "station or node name"

# §Description of Variables / ens_member
EXPECTED_ENS_MEMBER_STANDARD_NAME = "ens_member"
EXPECTED_ENS_MEMBER_LONG_NAME = "ensemble member"
EXPECTED_ENS_MEMBER_UNITS = "member id"
EXPECTED_ENS_MEMBER_AXIS = "u"

# §Description of Variables / lat
EXPECTED_LAT_LONG_NAME = "latitude"
EXPECTED_LAT_UNITS = "degrees_north"
EXPECTED_LAT_AXIS = "y"

# §Description of Variables / lon
EXPECTED_LON_LONG_NAME = "longitude"
EXPECTED_LON_UNITS = "degrees_east"
EXPECTED_LON_AXIS = "x"

# §Dimensions / strLen is fixed at 30 characters
EXPECTED_STR_LEN = 30

# §Description of Variables / lead_time attribute table
EXPECTED_LEAD_TIME_STANDARD_NAME = "lead time"
EXPECTED_LEAD_TIME_LONG_NAME = "forecast lead time"
EXPECTED_LEAD_TIME_AXIS = "u"  # convention table: axis = "u"
# Units template: "{timestep} since time" — timestep must match the lead step used
EXPECTED_LEAD_TIME_UNITS_DAYS = "days since time"
EXPECTED_LEAD_TIME_UNITS_HOURS = "hours since time"


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


def _temporary_named_file():
    """Create a temporary file, using RAM disk (/dev/shm) on Linux for faster tests."""
    if platform.system() == "Linux" and os.path.exists("/dev/shm"):
        return tempfile.NamedTemporaryFile(suffix=".nc", delete=False, dir="/dev/shm")
    return tempfile.NamedTemporaryFile(suffix=".nc", delete=False)


@pytest.fixture(scope="module")
def stf2_nc():
    """Module-scoped fixture: one minimal valid STF2 NetCDF file opened with netCDF4.

    Yields the open netCDF4.Dataset; closes and deletes the file after all tests
    in this module have run.
    """
    issue_times = pd.date_range("2024-06-01", periods=5, freq="D", tz="UTC")
    station_ids = [101, 202]
    lead_times = np.arange(1, 4)  # [1, 2, 3] — zero excluded per convention

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="days",
        ensemble_size=3,
        station_names=["Site_Alpha", "Site_Beta"],
        latitudes=[-33.5, -34.0],
        longitudes=[150.5, 151.0],
        nc_attributes={
            "title": "Coordinate attribute convention test",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Phase 1: testing coordinate variable attributes",
            "history": "Created for unit testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "q_var": {
                "name": "q_var",
                "longname": "streamflow",
                "units": "m3/s",
                "dim_type": "4",
                "missval": -9999.0,
                "precision": "double",
                "attributes": {},
            },
        }
    )
    eds.data["q_var"].loc[:, :, :, :] = np.ones((3, 2, 3, 5)) * 1.5

    with _temporary_named_file() as tmp:
        filename = tmp.name

    eds.save_to_stf2(
        path=filename,
        variable_name="q_var",
        var_type=StfVariable.STREAMFLOW,
        data_type=DataOriginType.OBSERVED,
        timestep="days",
    )

    ds = nc.Dataset(filename, "r")
    yield ds
    ds.close()
    if os.path.exists(filename):
        os.remove(filename)


# ---------------------------------------------------------------------------
# Phase 1, step 1 — time variable attributes
# ---------------------------------------------------------------------------


class TestTimeVariableAttributes:
    """Convention §Description of Variables / time attribute table."""

    def test_time_standard_name(self, stf2_nc):
        """standard_name must be 'time'."""
        assert stf2_nc.variables[TIME_DIMNAME].getncattr(STANDARD_NAME_ATTR_KEY) == EXPECTED_TIME_STANDARD_NAME

    def test_time_long_name(self, stf2_nc):
        """long_name must be 'time'."""
        assert stf2_nc.variables[TIME_DIMNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_TIME_LONG_NAME

    def test_time_axis(self, stf2_nc):
        """Convention axis label for time is 't'."""
        assert stf2_nc.variables[TIME_DIMNAME].getncattr(AXIS_ATTR_KEY) == EXPECTED_TIME_AXIS

    def test_time_units_present(self, stf2_nc):
        """units must be present and contain 'since' in CF-time format."""
        units = stf2_nc.variables[TIME_DIMNAME].getncattr(UNITS_ATTR_KEY)
        assert "since" in units

    def test_time_standard_attribute_contains_utc(self, stf2_nc):
        """time_standard must reference UTC."""
        time_standard = stf2_nc.variables[TIME_DIMNAME].getncattr("time_standard")
        assert "UTC" in time_standard


# ---------------------------------------------------------------------------
# Phase 1, step 2 — ens_member variable attributes
# ---------------------------------------------------------------------------


class TestEnsMemberVariableAttributes:
    """Convention §Description of Variables / ens_member attribute table."""

    def test_ens_member_standard_name(self, stf2_nc):
        """standard_name must be 'ens_member'."""
        assert (
            stf2_nc.variables[ENS_MEMBER_DIMNAME].getncattr(STANDARD_NAME_ATTR_KEY) == EXPECTED_ENS_MEMBER_STANDARD_NAME
        )

    def test_ens_member_long_name(self, stf2_nc):
        """long_name must be 'ensemble member'."""
        assert stf2_nc.variables[ENS_MEMBER_DIMNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_ENS_MEMBER_LONG_NAME

    def test_ens_member_units(self, stf2_nc):
        """units must be 'member id'."""
        assert stf2_nc.variables[ENS_MEMBER_DIMNAME].getncattr(UNITS_ATTR_KEY) == EXPECTED_ENS_MEMBER_UNITS

    def test_ens_member_axis(self, stf2_nc):
        """Convention axis label for ens_member is 'u'."""
        assert stf2_nc.variables[ENS_MEMBER_DIMNAME].getncattr(AXIS_ATTR_KEY) == EXPECTED_ENS_MEMBER_AXIS


# ---------------------------------------------------------------------------
# Phase 1, step 3 — station_id variable attributes
# ---------------------------------------------------------------------------


class TestStationIdVariableAttributes:
    """Convention §Description of Variables / station_id attribute table."""

    def test_station_id_long_name(self, stf2_nc):
        """long_name must be 'station or node identification code'."""
        assert stf2_nc.variables[STATION_ID_VARNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_STATION_ID_LONG_NAME


# ---------------------------------------------------------------------------
# Phase 1, step 4 — station_name variable attributes
# ---------------------------------------------------------------------------


class TestStationNameVariableAttributes:
    """Convention §Description of Variables / station_name attribute table."""

    def test_station_name_long_name(self, stf2_nc):
        """long_name must be 'station or node name'."""
        assert stf2_nc.variables[STATION_NAME_VARNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_STATION_NAME_LONG_NAME


# ---------------------------------------------------------------------------
# Phase 1, step 5 — lat variable attributes
# ---------------------------------------------------------------------------


class TestLatVariableAttributes:
    """Convention §Description of Variables / lat attribute table."""

    def test_lat_long_name(self, stf2_nc):
        """long_name must be 'latitude'."""
        assert stf2_nc.variables[LAT_VARNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_LAT_LONG_NAME

    def test_lat_units(self, stf2_nc):
        """units must be 'degrees_north'."""
        assert stf2_nc.variables[LAT_VARNAME].getncattr(UNITS_ATTR_KEY) == EXPECTED_LAT_UNITS

    def test_lat_axis(self, stf2_nc):
        """Convention axis label for lat is 'y'."""
        assert stf2_nc.variables[LAT_VARNAME].getncattr(AXIS_ATTR_KEY) == EXPECTED_LAT_AXIS


# ---------------------------------------------------------------------------
# Phase 1, step 6 — lon variable attributes
# ---------------------------------------------------------------------------


class TestLonVariableAttributes:
    """Convention §Description of Variables / lon attribute table."""

    def test_lon_long_name(self, stf2_nc):
        """long_name must be 'longitude'."""
        assert stf2_nc.variables[LON_VARNAME].getncattr(LONG_NAME_ATTR_KEY) == EXPECTED_LON_LONG_NAME

    def test_lon_units(self, stf2_nc):
        """units must be 'degrees_east'."""
        assert stf2_nc.variables[LON_VARNAME].getncattr(UNITS_ATTR_KEY) == EXPECTED_LON_UNITS

    def test_lon_axis(self, stf2_nc):
        """Convention axis label for lon is 'x'."""
        assert stf2_nc.variables[LON_VARNAME].getncattr(AXIS_ATTR_KEY) == EXPECTED_LON_AXIS


# ---------------------------------------------------------------------------
# Phase 1, step 7 — strLen dimension size
# ---------------------------------------------------------------------------


class TestStrLenDimension:
    """Convention §Dimensions: strLen is fixed at 30."""

    def test_strlen_dimension_is_present(self, stf2_nc):
        """strLen dimension must exist in written file."""
        assert STR_LEN_DIMNAME in stf2_nc.dimensions

    def test_strlen_dimension_equals_30(self, stf2_nc):
        """Convention specifies strLen = 30 (strings implemented as character arrays of length 30)."""
        assert len(stf2_nc.dimensions[STR_LEN_DIMNAME]) == EXPECTED_STR_LEN


# ---------------------------------------------------------------------------
# Phase 2 — lead_time.units matches the timestep parameter
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def stf2_nc_hourly():
    """Module-scoped fixture: minimal STF2 file saved with timestep='hours'.

    Used to verify that lead_time.units reflects the hourly time step rather
    than the hardcoded default.  Yields an open netCDF4.Dataset.
    """
    issue_times = pd.date_range("2024-06-01", periods=5, freq="h", tz="UTC")
    lead_times = [1, 6, 24]  # lead times expressed in hours; zero excluded per convention

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=[101, 202],
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=2,
        station_names=["Site_Alpha", "Site_Beta"],
        latitudes=[-33.5, -34.0],
        longitudes=[150.5, 151.0],
        nc_attributes={
            "title": "Hourly timestep convention test",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Phase 2: testing lead_time.units for hourly timestep",
            "history": "Created for unit testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "q_var": {
                "name": "q_var",
                "longname": "streamflow",
                "units": "m3/s",
                "dim_type": "4",
                "missval": -9999.0,
                "precision": "double",
                "attributes": {},
            },
        }
    )
    eds.data["q_var"].loc[:, :, :, :] = np.ones((3, 2, 2, 5)) * 1.5

    with _temporary_named_file() as tmp:
        filename = tmp.name

    eds.save_to_stf2(
        path=filename,
        variable_name="q_var",
        var_type=StfVariable.STREAMFLOW,
        data_type=DataOriginType.OBSERVED,
        timestep="hours",
    )

    ds = nc.Dataset(filename, "r")
    yield ds
    ds.close()
    if os.path.exists(filename):
        os.remove(filename)


class TestLeadTimeVariableAttributes:
    """Convention §Description of Variables / lead_time attribute table.

    The convention requires:
        standard_name : "lead time"
        long_name     : "forecast lead time"
        units         : "{timestep} since time"   (hours/days/months)
        axis          : "u"

    Tests use the daily fixture (stf2_nc) for the stable attributes and both
    fixtures for the units check.
    """

    def test_lead_time_standard_name(self, stf2_nc):
        """standard_name must be 'lead time'."""
        assert (
            stf2_nc.variables[LEAD_TIME_DIMNAME].getncattr(STANDARD_NAME_ATTR_KEY)
            == EXPECTED_LEAD_TIME_STANDARD_NAME
        )

    def test_lead_time_long_name(self, stf2_nc):
        """long_name must be 'forecast lead time'."""
        assert (
            stf2_nc.variables[LEAD_TIME_DIMNAME].getncattr(LONG_NAME_ATTR_KEY)
            == EXPECTED_LEAD_TIME_LONG_NAME
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Convention §lead_time: axis must be 'u'. "
            "Implementation currently writes 'v'. "
            "Bug tracked in test_write_stf.py::test_save_to_stf2_preserves_data_array_attributes."
        ),
    )
    def test_lead_time_axis(self, stf2_nc):
        """Convention axis label for lead_time is 'u'."""
        assert (
            stf2_nc.variables[LEAD_TIME_DIMNAME].getncattr(AXIS_ATTR_KEY)
            == EXPECTED_LEAD_TIME_AXIS
        )

    def test_lead_time_units_days(self, stf2_nc):
        """Convention: units must be 'days since time' when timestep='days'.

        The daily fixture (stf2_nc) is saved with timestep='days'.
        The hardcoded implementation already produces 'days since time', so this passes.
        """
        assert (
            stf2_nc.variables[LEAD_TIME_DIMNAME].getncattr(UNITS_ATTR_KEY)
            == EXPECTED_LEAD_TIME_UNITS_DAYS
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Convention §lead_time: units must be '{timestep} since time'. "
            "When timestep='hours' the units should be 'hours since time', "
            "but the implementation hardcodes 'days since time' regardless of timestep."
        ),
    )
    def test_lead_time_units_hours(self, stf2_nc_hourly):
        """Convention: units must be 'hours since time' when timestep='hours'.

        The hourly fixture (stf2_nc_hourly) is saved with timestep='hours'.
        Per the STF 2.0 convention the units attribute must reflect the lead time
        step (NB#1: unit of lead_time does not have to equal the unit of time, but
        when both are controlled by the same `timestep` argument the units should
        match).  The current implementation hardcodes 'days since time', so this
        test is expected to fail until the bug is resolved.
        """
        assert (
            stf2_nc_hourly.variables[LEAD_TIME_DIMNAME].getncattr(UNITS_ATTR_KEY)
            == EXPECTED_LEAD_TIME_UNITS_HOURS
        )


# ---------------------------------------------------------------------------
# Phase 5 — Optional geolocation variable attributes
# ---------------------------------------------------------------------------

# Convention §Description of Variables / area, elevation, x, y:
# Each optional variable, when present, must carry standard_name, long_name, units.
# xr_efts always creates area; elevation, x, y are absent unless manually added.

_OPTIONAL_GEOLOCATION_VARS = ["area"]  # only 'area' is created by xr_efts by default


class TestOptionalGeolocationVariableAttributes:
    """Convention §Optional Variables: area (and by extension elevation, x, y) must carry
    standard_name, long_name, and units when present in the written file.
    """

    @pytest.mark.parametrize("var_name", _OPTIONAL_GEOLOCATION_VARS)
    def test_optional_var_has_standard_name(self, stf2_nc, var_name):
        """standard_name attribute must be present on optional geolocation variable."""
        assert var_name in stf2_nc.variables, f"Variable '{var_name}' not found in written file."
        assert STANDARD_NAME_ATTR_KEY in stf2_nc.variables[var_name].ncattrs(), (
            f"Missing 'standard_name' on optional variable '{var_name}'."
        )

    @pytest.mark.parametrize("var_name", _OPTIONAL_GEOLOCATION_VARS)
    def test_optional_var_has_long_name(self, stf2_nc, var_name):
        """long_name attribute must be present on optional geolocation variable."""
        assert var_name in stf2_nc.variables, f"Variable '{var_name}' not found in written file."
        assert LONG_NAME_ATTR_KEY in stf2_nc.variables[var_name].ncattrs(), (
            f"Missing 'long_name' on optional variable '{var_name}'."
        )

    @pytest.mark.parametrize("var_name", _OPTIONAL_GEOLOCATION_VARS)
    def test_optional_var_has_units(self, stf2_nc, var_name):
        """units attribute must be present on optional geolocation variable."""
        assert var_name in stf2_nc.variables, f"Variable '{var_name}' not found in written file."
        assert UNITS_ATTR_KEY in stf2_nc.variables[var_name].ncattrs(), (
            f"Missing 'units' on optional variable '{var_name}'."
        )

    def test_area_dimension_is_station(self, stf2_nc):
        """Convention: area variable must have dimension (station,)."""
        assert stf2_nc.variables["area"].dimensions == ("station",)
