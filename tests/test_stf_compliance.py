"""Convention-driven tests for check_stf_compliance().

Tests are derived from the STF 2.0 conventions specification
(https://github.com/csiro-hydroinformatics/efts-io/blob/42ee35f0f019e9bad48b94914429476a7e8278dc/docs/netcdf_for_water_forecasting.md),
not from the implementation.

Phase 6 — check_stf_compliance()
  check_stf_compliance(file_path) returns a dict with keys "INFO", "WARNING", "ERROR".
  Convention §Dimensions: missing required dimension → ERROR.
  Convention §Global Attributes: missing global attribute → WARNING.
  Convention §Mandatory Variables: missing mandatory variable → ERROR.
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
    CATCHMENT_ATTR_KEY,
    ENS_MEMBER_DIMNAME,
    LAT_VARNAME,
    LEAD_TIME_DIMNAME,
    LON_VARNAME,
    STATION_DIMNAME,
    STATION_ID_VARNAME,
    STATION_NAME_VARNAME,
    STR_LEN_DIMNAME,
    TIME_DIMNAME,
    DataOriginType,
    check_stf_compliance,
)
from efts_io.wrapper import EftsDataSet, xr_efts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temporary_named_file():
    """Create a temporary file, using RAM disk (/dev/shm) on Linux for faster tests."""
    if platform.system() == "Linux" and os.path.exists("/dev/shm"):
        return tempfile.NamedTemporaryFile(suffix=".nc", delete=False, dir="/dev/shm")
    return tempfile.NamedTemporaryFile(suffix=".nc", delete=False)


def _write_valid_stf2_file(filename: str) -> None:
    """Write a minimal but fully valid STF2 NetCDF file to *filename*."""
    issue_times = pd.date_range("2024-01-01", periods=4, freq="D", tz="UTC")

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=[1, 2],
        lead_times=[1, 2, 3],
        lead_time_tstep="days",
        ensemble_size=2,
        station_names=["Site_A", "Site_B"],
        latitudes=[-33.0, -34.0],
        longitudes=[150.0, 151.0],
        nc_attributes={
            "title": "STF compliance test",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Phase 6: testing check_stf_compliance",
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
    eds.data["q_var"].loc[:, :, :, :] = np.ones((3, 2, 2, 4)) * 1.0
    eds.save_to_stf2(
        path=filename,
        variable_name="q_var",
        var_type=StfVariable.STREAMFLOW,
        data_type=DataOriginType.OBSERVED,
        timestep="days",
    )


def _write_file_missing_dimension(filename: str, omit_dim: str) -> None:
    """Write a bare-minimum NetCDF4 file that is missing *omit_dim*.

    Creates only the required STF2 dimensions except the given one, with no
    real data — sufficient to trigger the dimension-check logic in
    check_stf_compliance.
    """
    required_dims = {
        TIME_DIMNAME: 4,
        STATION_DIMNAME: 2,
        LEAD_TIME_DIMNAME: 3,
        ENS_MEMBER_DIMNAME: 2,
        STR_LEN_DIMNAME: 30,
    }
    with nc.Dataset(filename, "w", format="NETCDF4") as ds:
        for dim, size in required_dims.items():
            if dim != omit_dim:
                ds.createDimension(dim, size)


def _write_file_missing_variable(filename: str, omit_var: str) -> None:
    """Write a valid STF2 file then re-open it and delete *omit_var*.

    netCDF4 does not support deleting variables from an existing file, so
    we instead produce a fresh file using the classic (non-netCDF4 HDF5)
    NETCDF3_CLASSIC format and simply omit the variable when writing.
    """
    required_dims = {
        TIME_DIMNAME: 4,
        STATION_DIMNAME: 2,
        LEAD_TIME_DIMNAME: 3,
        ENS_MEMBER_DIMNAME: 2,
        STR_LEN_DIMNAME: 30,
    }
    mandatory_vars = {
        TIME_DIMNAME: (TIME_DIMNAME,),
        STATION_ID_VARNAME: (STATION_DIMNAME,),
        STATION_NAME_VARNAME: (STR_LEN_DIMNAME, STATION_DIMNAME),
        ENS_MEMBER_DIMNAME: (ENS_MEMBER_DIMNAME,),
        LEAD_TIME_DIMNAME: (LEAD_TIME_DIMNAME,),
        LAT_VARNAME: (STATION_DIMNAME,),
        LON_VARNAME: (STATION_DIMNAME,),
    }
    with nc.Dataset(filename, "w", format="NETCDF4") as ds:
        for dim, size in required_dims.items():
            ds.createDimension(dim, size)
        for var, dims in mandatory_vars.items():
            if var != omit_var:
                ds.createVariable(var, "f", dims)


# ---------------------------------------------------------------------------
# Phase 6, step 13 — valid file produces no ERRORs
# ---------------------------------------------------------------------------


class TestCheckStfComplianceValidFile:
    """A fully conformant STF2 file must produce no ERRORs."""

    @pytest.fixture(scope="class")
    def valid_result(self):
        with _temporary_named_file() as tmp:
            filename = tmp.name
        try:
            _write_valid_stf2_file(filename)
            yield check_stf_compliance(filename)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_no_errors(self, valid_result):
        """Convention: a fully compliant file must produce no ERRORs."""
        assert valid_result["ERROR"] == []

    def test_result_has_expected_keys(self, valid_result):
        """Return value must have exactly the keys INFO, WARNING, ERROR."""
        assert set(valid_result.keys()) == {"INFO", "WARNING", "ERROR"}

    def test_required_dimensions_reported_as_info(self, valid_result):
        """Each required dimension present in a valid file appears in INFO."""
        info_text = " ".join(valid_result["INFO"])
        for dim in (TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, ENS_MEMBER_DIMNAME, STR_LEN_DIMNAME):
            assert dim in info_text, f"Expected dimension '{dim}' to appear in INFO messages."


# ---------------------------------------------------------------------------
# Phase 6, step 14 — missing required dimension → ERROR
# ---------------------------------------------------------------------------


class TestCheckStfComplianceMissingDimension:
    """Convention §Dimensions: each of the 5 required dimensions must be present;
    absence is reported as an ERROR."""

    @pytest.mark.parametrize(
        "omit_dim",
        [TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME, ENS_MEMBER_DIMNAME, STR_LEN_DIMNAME],
    )
    def test_missing_dimension_reported_as_error(self, omit_dim):
        """A file missing a required dimension must have at least one ERROR
        and that ERROR message must name the missing dimension."""
        with _temporary_named_file() as tmp:
            filename = tmp.name
        try:
            _write_file_missing_dimension(filename, omit_dim)
            result = check_stf_compliance(filename)
            assert len(result["ERROR"]) > 0, (
                f"Expected an ERROR for missing dimension '{omit_dim}', got none."
            )
            assert any(omit_dim in msg for msg in result["ERROR"]), (
                f"Expected the ERROR message to mention '{omit_dim}'. Got: {result['ERROR']}"
            )
        finally:
            if os.path.exists(filename):
                os.remove(filename)


# ---------------------------------------------------------------------------
# Phase 6, step 15 — missing global attribute → WARNING
# ---------------------------------------------------------------------------


class TestCheckStfComplianceMissingGlobalAttribute:
    """Convention §Global Attributes: missing global attribute is reported as a WARNING
    (not an ERROR — the function's documented classification)."""

    def test_missing_global_attribute_reported_as_warning(self):
        """A file whose catchment global attribute has been removed must produce
        a WARNING that names the missing attribute."""
        with _temporary_named_file() as tmp:
            filename = tmp.name
        try:
            _write_valid_stf2_file(filename)
            # Re-open in write mode to delete the attribute
            with nc.Dataset(filename, "a") as ds:
                ds.delncattr(CATCHMENT_ATTR_KEY)

            result = check_stf_compliance(filename)
            assert any(CATCHMENT_ATTR_KEY in msg for msg in result["WARNING"]), (
                f"Expected a WARNING mentioning '{CATCHMENT_ATTR_KEY}'. Got: {result['WARNING']}"
            )
        finally:
            if os.path.exists(filename):
                os.remove(filename)


# ---------------------------------------------------------------------------
# Phase 6, step 16 — missing mandatory variable → ERROR
# ---------------------------------------------------------------------------


class TestCheckStfComplianceMissingVariable:
    """Convention §Mandatory Variables: each mandatory variable must be present;
    absence is reported as an ERROR."""

    @pytest.mark.parametrize(
        "omit_var",
        [LAT_VARNAME, LON_VARNAME, STATION_ID_VARNAME, STATION_NAME_VARNAME],
    )
    def test_missing_mandatory_variable_reported_as_error(self, omit_var):
        """A file missing a mandatory variable must have at least one ERROR
        and that ERROR message must name the missing variable."""
        with _temporary_named_file() as tmp:
            filename = tmp.name
        try:
            _write_file_missing_variable(filename, omit_var)
            result = check_stf_compliance(filename)
            assert len(result["ERROR"]) > 0, (
                f"Expected an ERROR for missing variable '{omit_var}', got none."
            )
            assert any(omit_var in msg for msg in result["ERROR"]), (
                f"Expected the ERROR message to mention '{omit_var}'. Got: {result['ERROR']}"
            )
        finally:
            if os.path.exists(filename):
                os.remove(filename)
