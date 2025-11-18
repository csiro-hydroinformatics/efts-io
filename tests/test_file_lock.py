"""Test that file locks are properly released on errors in save_to_stf2."""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from efts_io._ncdf_stf2 import StfDataType, StfVariable
from efts_io.wrapper import EftsDataSet, xr_efts


def test_file_lock_released_on_validation_error() -> None:
    """Test that no file is created when validation error occurs before write.

    This test verifies that when an error occurs in save_to_stf2 before
    the file is opened, no file is created.
    """
    # Create test data with valid station IDs
    xr_ds = xr_efts(
        issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
        station_ids=[1, 2, 3],
        lead_times=np.arange(start=1, stop=4, step=1),
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["station_1", "station_2", "station_3"],
        nc_attributes={
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "history": "Created for testing purposes",
            "references": "None",
            "comment": "This is a test dataset",
            "catchment": "Test catchment",
        },
        areas=[10.0, 20.0, 30.0],
        latitudes=[60.0, 61.0, 62.0],
        longitudes=[10.0, 11.0, 12.0],
    )

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "rain_obs": {
                "name": "rain_obs",
                "longname": "Observed Rainfall Amount",
                "units": "mm",
                "dim_type": "4",
                "comment": "This is a comment for the variable",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        },
    )

    # Use a filename that doesn't exist yet (don't create it with tempfile)
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "test_output.nc")

        # First attempt: Force a failure by using an invalid variable name
        # This should raise a KeyError but not leave the file locked
        with pytest.raises(KeyError):
            eds.save_to_stf2(
                path=filename,
                variable_name="nonexistent_variable",  # This will fail
                var_type=StfVariable.RAINFALL,
                data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
                ens=False,
                timestep="hours",
                data_qual=None,
            )

        # Verify that the file was not created (error happened before file creation)
        assert not os.path.exists(filename), "File should not be created on early validation error"

        # Second attempt: Now try with the correct variable name
        # This should succeed without permission errors
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
            ens=False,
            timestep="hours",
            data_qual=None,
        )

        # Verify the file was created successfully
        assert os.path.exists(filename), "File should exist after successful save"

        # Verify we can read the file back
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars


def test_file_lock_released_on_write_error() -> None:
    """Test that file lock is released when an error occurs during write.

    This test creates a situation where the netCDF file is opened but
    an error occurs during writing, and verifies the file is cleaned up
    and can be written to successfully on retry.
    """
    # Create test data with missing required global attributes
    # This will pass initial validation but fail during write_nc_stf2
    xr_ds = xr_efts(
        issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
        station_ids=[1, 2, 3],
        lead_times=np.arange(start=1, stop=4, step=1),
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["station_1", "station_2", "station_3"],
        nc_attributes={
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "history": "Created for testing purposes",
            "references": "None",
            "comment": "This is a test dataset",
            "catchment": "Test catchment",
        },
        areas=[10.0, 20.0, 30.0],
        latitudes=[60.0, 61.0, 62.0],
        longitudes=[10.0, 11.0, 12.0],
    )

    # Intentionally remove a required attribute to cause an error in write_nc_stf2
    del xr_ds.attrs["title"]

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "rain_obs": {
                "name": "rain_obs",
                "longname": "Observed Rainfall Amount",
                "units": "mm",
                "dim_type": "4",
                "comment": "This is a comment for the variable",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        },
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "test_output.nc")

        # First attempt: This should fail during write_nc_stf2
        # The file will be created and opened, but writing should fail
        with pytest.raises(ValueError, match="DataArray must have the following global attributes"):
            eds.save_to_stf2(
                path=filename,
                variable_name="rain_obs",
                var_type=StfVariable.RAINFALL,
                data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
                ens=False,
                timestep="hours",
                data_qual=None,
            )

        # Verify that the file was cleaned up after the error
        assert not os.path.exists(filename), "Partially written file should be removed after write error"

        # Now create a proper dataset with all required attributes
        xr_ds2 = xr_efts(
            issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
            station_ids=[1, 2, 3],
            lead_times=np.arange(start=1, stop=4, step=1),
            lead_time_tstep="hours",
            ensemble_size=1,
            station_names=["station_1", "station_2", "station_3"],
            nc_attributes={
                "title": "Test dataset",
                "institution": "Test institution",
                "source": "Test source",
                "history": "Created for testing purposes",
                "references": "None",
                "comment": "This is a test dataset",
                "catchment": "Test catchment",
            },
            areas=[10.0, 20.0, 30.0],
            latitudes=[60.0, 61.0, 62.0],
            longitudes=[10.0, 11.0, 12.0],
        )

        eds2 = EftsDataSet(xr_ds2)
        eds2.create_data_variables(
            {
                "rain_obs": {
                    "name": "rain_obs",
                    "longname": "Observed Rainfall Amount",
                    "units": "mm",
                    "dim_type": "4",
                    "comment": "This is a comment for the variable",
                    "missval": np.nan,
                    "precision": "double",
                    "attributes": {},
                },
            },
        )

        # Second attempt: This should succeed without permission errors
        eds2.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
            ens=False,
            timestep="hours",
            data_qual=None,
        )

        # Verify the file was created successfully
        assert os.path.exists(filename), "File should exist after successful save"

        # Verify we can read the file back
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars


def test_file_lock_released_on_overflow_error() -> None:
    """Test that file lock is released when station ID overflow error occurs.

    This test verifies that after an OverflowError due to large station IDs,
    the file lock is properly released.
    """
    # Create test data with station IDs that will overflow int32
    large_station_ids = [1, 2, 999999999999]  # Last ID is too large for int32

    xr_ds = xr_efts(
        issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
        station_ids=large_station_ids,
        lead_times=np.arange(start=1, stop=4, step=1),
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["station_1", "station_2", "station_3"],
        nc_attributes={
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "history": "Created for testing purposes",
            "references": "None",
            "comment": "This is a test dataset",
            "catchment": "Test catchment",
        },
        areas=[10.0, 20.0, 30.0],
        latitudes=[60.0, 61.0, 62.0],
        longitudes=[10.0, 11.0, 12.0],
    )

    eds = EftsDataSet(xr_ds)
    eds.stf2_int_datatype = "i4"  # Use int32 to trigger overflow
    eds.create_data_variables(
        {
            "rain_obs": {
                "name": "rain_obs",
                "longname": "Observed Rainfall Amount",
                "units": "mm",
                "dim_type": "4",
                "comment": "This is a comment for the variable",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        },
    )

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        # First attempt: This should raise an OverflowError due to large station IDs
        with pytest.raises(OverflowError):
            eds.save_to_stf2(
                path=filename,
                variable_name="rain_obs",
                var_type=StfVariable.RAINFALL,
                data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
                ens=False,
                timestep="hours",
                data_qual=None,
            )

        # Verify that the file was cleaned up after the error
        assert not os.path.exists(filename), "Partially written file should be removed after overflow error"

        # Now create a dataset with valid station IDs
        xr_ds2 = xr_efts(
            issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
            station_ids=[1, 2, 3],
            lead_times=np.arange(start=1, stop=4, step=1),
            lead_time_tstep="hours",
            ensemble_size=1,
            station_names=["station_1", "station_2", "station_3"],
            nc_attributes={
                "title": "Test dataset",
                "institution": "Test institution",
                "source": "Test source",
                "history": "Created for testing purposes",
                "references": "None",
                "comment": "This is a test dataset",
                "catchment": "Test catchment",
            },
            areas=[10.0, 20.0, 30.0],
            latitudes=[60.0, 61.0, 62.0],
            longitudes=[10.0, 11.0, 12.0],
        )

        eds2 = EftsDataSet(xr_ds2)
        eds2.create_data_variables(
            {
                "rain_obs": {
                    "name": "rain_obs",
                    "longname": "Observed Rainfall Amount",
                    "units": "mm",
                    "dim_type": "4",
                    "comment": "This is a comment for the variable",
                    "missval": np.nan,
                    "precision": "double",
                    "attributes": {},
                },
            },
        )

        # Second attempt: Now try with valid station IDs
        # This should succeed without permission errors
        eds2.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
            ens=False,
            timestep="hours",
            data_qual=None,
        )

        # Verify the file was created successfully
        assert os.path.exists(filename), "File should exist after successful save"

        # Verify we can read the file back
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars

    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
