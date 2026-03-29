from os import read
from typing import Iterable
import pytest
import numpy as np
import pytz
import xarray as xr
from efts_io._ncdf_stf2 import make_ready_for_saving
import pandas as pd

from efts_io.conventions import (
    ENS_MEMBER_DIMNAME,
    STATION_DIMNAME,
    TIME_DIMNAME,
    STATION_ID_DIMNAME,
    LEAD_TIME_DIMNAME,
    REALISATION_DIMNAME,
    STATION_NAME_VARNAME,
    LAT_VARNAME,
    LON_VARNAME,
    DataOriginType,
    xr_to_stf_dims,
    stf_to_xr_dims,
)


def sample_dataset(
    n_time=5,
    n_stations=2,
    n_lead_time=3,
    n_realisations=4,
    time_zone=None,
):
    """Create a sample dataset with all required coordinates."""
    stations_nbs = np.arange(n_stations)
    ds = xr.Dataset(
        coords={
            TIME_DIMNAME: pd.date_range("2023-01-01", periods=n_time, tz=time_zone),
            STATION_ID_DIMNAME: [f"station_{i}" for i in range(n_stations)],
            LEAD_TIME_DIMNAME: list(range(n_lead_time)),
            REALISATION_DIMNAME: list(range(n_realisations)),
        },
        data_vars={
            # STATION_ID_VARNAME: xr.DataArray([1, 2, 3], dims=[STATION_ID_DIMNAME]),
            STATION_NAME_VARNAME: xr.DataArray(
                [f"station_{i} name" for i in range(n_stations)], dims=[STATION_ID_DIMNAME]
            ),
            LAT_VARNAME: xr.DataArray(1.1 * stations_nbs, dims=[STATION_ID_DIMNAME]),
            LON_VARNAME: xr.DataArray(100.0 + stations_nbs, dims=[STATION_ID_DIMNAME]),
        },
    )
    return ds


def stf_dimensions_order():
    """Return the standard STF dimensions order for NetCDF files."""
    return (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)


def xr_dimensions_order():
    """Return the corresponding xarray dimensions order."""
    return (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)


import numpy as np
import xarray as xr


def create_data_array(
    stf_equivalent_dimensions: Iterable[str],
    dataset: xr.Dataset,
) -> xr.DataArray:
    """Helper function to create a test DataArray with specific dimensions.

    Args:
        stf_equivalent_dimensions (list): List of dimension names in STF equivalent order.
          The sample data will be created with equivalent dimensions in the xarray form
        dataset (xr.Dataset, optional): Dataset to use for coordinates if available.

    Returns:
        xr.DataArray: DataArray with specified dimensions and data.
    """
    xr_dimensions = [stf_to_xr_dims[x] if x in stf_to_xr_dims else x for x in stf_equivalent_dimensions]
    if dataset is not None:
        dimsizes = {x: len(dataset.coords[x]) if x in xr_to_stf_dims else 2 for x in xr_dimensions}
    else:
        dimsizes = {}
    shape = tuple(dimsizes[dim] if dim in dimsizes else 2 for dim in xr_dimensions)

    # Create data with the specified shape based on dimension indices
    data = np.zeros(shape)
    for idx, dim in enumerate(xr_dimensions):
        if dim == TIME_DIMNAME:
            data += 1 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == STATION_ID_DIMNAME:
            data += 0.1 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == LEAD_TIME_DIMNAME:
            data += 0.01 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == REALISATION_DIMNAME:
            data += 0.001 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])

    # If dataset is provided, use its coordinates
    if dataset is not None:
        coords = {dim: dataset[dim] if dim in dataset.coords else np.arange(2) for dim in xr_dimensions}
        return xr.DataArray(data, dims=xr_dimensions, coords=coords)
    else:
        return xr.DataArray(data, dims=xr_dimensions)


# mini tests for the test dataset creators:


def test_create_data_array_with_all_dimensions():
    """Test the creation of a DataArray with all specified dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    stf_equivalent_dimensions = stf_dimensions_order()
    data_array = create_data_array(stf_equivalent_dimensions, dataset)

    assert data_array.dims == xr_dimensions_order()
    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert data_array.shape == (5, 4, 2, 3)


def test_create_data_array_with_missing_dimensions():
    """Test the creation of a DataArray with missing dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    stf_equivalent_dimensions = (TIME_DIMNAME, STATION_DIMNAME)
    data_array = create_data_array(stf_equivalent_dimensions, dataset)

    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert data_array.dims == (TIME_DIMNAME, STATION_ID_DIMNAME)
    assert data_array.shape == (5, 2)


def test_create_data_array_without_dataset():
    """Test the creation of a DataArray without a dataset."""
    stf_equivalent_dimensions = (TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME)
    data_array = create_data_array(stf_equivalent_dimensions, None)

    assert data_array.dims == (TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME)
    assert data_array.shape == (2, 2, 2, 2)  # Default shape when dataset is None


# Testing `make_ready_for_saving`


def _check_all_four_dims(dimensions_order):
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    data = create_data_array(dimensions_order, dataset)
    result = make_ready_for_saving(data, dataset, stf_dimensions_order())

    assert result.dims == xr_dimensions_order()
    assert result.shape == (5, 4, 2, 3)


def test_presave_with_all_dimensions_standard_order():
    """Test the transformation of a DataArray with all required dimensions."""
    dimensions_order = stf_dimensions_order()
    _check_all_four_dims(dimensions_order)


def test_presave_with_all_dimensions_different_order():
    """Test the transformation of a DataArray with all required dimensions."""
    dimensions_order = stf_dimensions_order()[::-1]
    _check_all_four_dims(dimensions_order)


def test_presave_with_missing_dimensions():
    """Test the transformation of a DataArray with missing dimensions."""
    a_dimensions = (TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
    # no ENS_MEMBER_DIMNAME,
    # First, let us assume a the dataset has a ENS_MEMBER_DIMNAME dim of 1
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=1)
    data = create_data_array(a_dimensions, dataset)
    result = make_ready_for_saving(data, dataset, stf_dimensions_order())
    assert result.dims == xr_dimensions_order()
    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert result.shape == (5, 1, 2, 3)
    # however if the dataset has more than one realisation, this is problematic
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=3)
    data = create_data_array(a_dimensions, dataset)
    with pytest.raises(ValueError):
        result = make_ready_for_saving(data, dataset, stf_dimensions_order())


def test_presave_with_invalid_dimensions():
    """Test the transformation of a DataArray with invalid dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    data = xr.DataArray(np.random.rand(5, 2), dims=(TIME_DIMNAME, "invalid_dim"))
    dimensions_order = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)

    with pytest.raises(ValueError):
        _ = make_ready_for_saving(data, dataset, stf_dimensions_order())

    # TODO: following a tad superfluous perhaps, and cannot get the test data creation to work yet
    # data_dimensions = ("invalid_dim",) + dimensions_order
    # data = create_data_array(data_dimensions, dataset)
    # with pytest.raises(ValueError):
    #     _ = make_ready_for_saving(data, dataset, stf_dimensions_order())


# Testing `exportable_to_stf2`


def create_valid_stf2_dataset(time_zone=None):
    """Create a dataset with all required dimensions, variables, and attributes for STF 2.0."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4, time_zone=time_zone)

    # Add required global attributes
    dataset.attrs.update(
        {
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "catchment": "Test catchment",
            "comment": "Test comment",
            "history": "Test history",
        }
    )

    return dataset


def test_exportable_to_stf2_valid_dataset():
    """Test that a valid dataset with all required components returns True."""
    from efts_io.conventions import exportable_to_stf2

    dataset = create_valid_stf2_dataset()
    assert exportable_to_stf2(dataset) is True
    dataset = create_valid_stf2_dataset(time_zone="UTC+01:00")
    assert exportable_to_stf2(dataset) is True
    dataset = create_valid_stf2_dataset(time_zone="UTC+09:30")
    assert exportable_to_stf2(dataset) is True


def test_exportable_to_stf2_valid_dataset_unsupported_timezone():
    dataset = create_valid_stf2_dataset(time_zone="Australia/Sydney")
    from efts_io.conventions import exportable_to_stf2

    assert exportable_to_stf2(dataset) is False, (
        "Australia/Sydney is a timezone-aware timestamp that includes daylight saving time changes, which is currently not supported by exportable_to_stf2. "
    )


def test_exportable_to_stf2_missing_dimensions():
    """Test that a dataset with missing dimensions returns False."""
    from efts_io.conventions import exportable_to_stf2

    dataset = create_valid_stf2_dataset()
    # Remove a required dimension by creating a new dataset without it
    dataset_missing_dim = dataset.drop_dims(LEAD_TIME_DIMNAME)

    assert exportable_to_stf2(dataset_missing_dim) is False


def test_exportable_to_stf2_missing_global_attributes():
    """Test that a dataset with missing global attributes returns False."""
    from efts_io.conventions import exportable_to_stf2

    dataset = create_valid_stf2_dataset()
    # Remove a required global attribute
    del dataset.attrs["title"]

    assert exportable_to_stf2(dataset) is False


def test_exportable_to_stf2_missing_variables():
    """Test that a dataset with missing required variables returns False."""
    from efts_io.conventions import exportable_to_stf2

    dataset = create_valid_stf2_dataset()
    # Remove a required variable
    dataset = dataset.drop_vars(LAT_VARNAME)

    assert exportable_to_stf2(dataset) is False


def test_exportable_to_stf2_string_station_ids():
    """Test that a dataset with string station_ids is supported."""
    from efts_io.conventions import exportable_to_stf2

    # Create a dataset but keep the string station_ids (as created by sample_dataset)
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    dataset.attrs.update(
        {
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "catchment": "Test catchment",
            "comment": "Test comment",
            "history": "Test history",
        }
    )
    # check the test dataset station_ids are strings
    assert np.issubdtype(dataset[STATION_ID_DIMNAME].values.dtype, np.str_) is True
    assert exportable_to_stf2(dataset) is True


def test_exportable_to_stf2_integer_station_ids():
    """Test that a dataset with integer station_ids returns True."""
    from efts_io.conventions import exportable_to_stf2

    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)

    # Replace string station_ids with integers
    dataset = dataset.assign_coords({STATION_ID_DIMNAME: [1, 2]})

    dataset.attrs.update(
        {
            "title": "Test dataset",
            "institution": "Test institution",
            "source": "Test source",
            "catchment": "Test catchment",
            "comment": "Test comment",
            "history": "Test history",
        }
    )

    assert exportable_to_stf2(dataset) is True


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Convention §Description of Variables / lead_time: "
        "'lead_time zero is the same date and time as the time dimension and therefore "
        "not expected as a legitimate value.' "
        "exportable_to_stf2 does not currently validate against zero lead_time values."
    ),
)
def test_exportable_to_stf2_rejects_zero_lead_time():
    """Convention: a lead_time coordinate containing zero must not be exportable.

    The STF 2.0 spec states that lead_time zero is implicitly the same instant as
    the time dimension and is therefore never a legitimate value in the lead_time
    variable.  exportable_to_stf2 should return False for such datasets.
    """
    from efts_io.conventions import exportable_to_stf2

    dataset = create_valid_stf2_dataset()
    # Introduce zero into the lead_time coordinate — convention says this is invalid
    dataset = dataset.assign_coords({LEAD_TIME_DIMNAME: [0, 1, 2]})

    assert exportable_to_stf2(dataset) is False


def _temporary_named_file():
    """Create a temporary file, using RAM disk (/dev/shm) on Linux for faster tests."""
    import platform
    import tempfile
    import os

    # Use RAM disk on Linux if available
    if platform.system() == "Linux" and os.path.exists("/dev/shm"):
        return tempfile.NamedTemporaryFile(suffix=".nc", delete=False, dir="/dev/shm")
    else:
        return tempfile.NamedTemporaryFile(suffix=".nc", delete=False)


def test_station_id_int64_preserved_on_read():
    """Test that int64 station_id values are not converted to float64 when reading from STF2 files.

    Reproduces issue where xarray converts int64 station_id variables with _FillValue
    to float64 when reading netCDF files with default mask_and_scale=True.

    This test:
    1. Creates a dataset with large int64 station_ids
    2. Saves to STF2 netCDF file with i8 (int64) data type
    3. Reads back the raw file with xarray
    4. Validates that station_id has incorrect float64 dtype (reproducing the bug)
    5. Validates that with mask_and_scale=False, int64 is preserved (the fix)
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import STATION_ID_VARNAME

    # 1. Create test data with large int64 station IDs that exceed int32 range
    issue_times = pd.date_range("2023-01-01", periods=10, freq="D")
    station_ids = [123456789123, 987654321987]  # Large int64 values
    lead_times = np.arange(1, 4)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["station_A", "station_B"],
        nc_attributes={
            "title": "Test dataset for int64 dtype preservation",
            "institution": "Test",
            "source": "Unit test",
            "catchment": "Test catchment",
            "comment": "Test for station_id int64 dtype preservation",
            "history": "Created for testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.stf2_int_datatype = "i8"  # Use int64 for large values

    # Add a data variable (required for save_to_stf2)
    eds.create_data_variables(
        {
            "rain_obs": {
                "name": "rain_obs",
                "longname": "Rainfall",
                "units": "mm",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    # populate some values for the data variable, a mix of missing values and real values
    eds.data["rain_obs"].loc[:, :, :, :] = np.random.rand(3, 2, 1, 10) * 10.0
    # Use actual coordinate values: lead_time=1, station_id=first station, all realisations, time=first time
    eds.data["rain_obs"].loc[1, station_ids[0], :, issue_times[0]] = np.nan  # introduce a missing value

    # 2. Save to STF2 file
    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.OBSERVED,
        )

        # 3. Read back with default xarray settings (reproduces the bug)
        raw_ds_with_bug = xr.open_dataset(filename, decode_times=False)
        raw_station_ids_buggy = raw_ds_with_bug[STATION_ID_VARNAME].values

        # 4. THIS IS THE BUG: station_id should be int64, but xarray converts to float64
        # because of _FillValue with default mask_and_scale=True
        assert raw_station_ids_buggy.dtype == np.float64, (
            f"Bug not reproduced! Expected float64 (the bug), got {raw_station_ids_buggy.dtype}. "
            "This test validates the bug exists before applying the fix."
        )

        # Values are still correct numerically (but as floats)
        np.testing.assert_array_almost_equal(raw_station_ids_buggy, station_ids)

        raw_ds_with_bug.close()

        # 5. THE FIX: Read with mask_and_scale=False to preserve int64
        raw_ds_fixed = xr.open_dataset(filename, decode_times=False, mask_and_scale=False)
        raw_station_ids_fixed = raw_ds_fixed[STATION_ID_VARNAME].values

        # With the fix, dtype should be int64
        assert np.issubdtype(raw_station_ids_fixed.dtype, np.integer), (
            f"Expected integer dtype with mask_and_scale=False, got {raw_station_ids_fixed.dtype}"
        )
        assert raw_station_ids_fixed.dtype == np.int64, (
            f"Expected int64 with mask_and_scale=False, got {raw_station_ids_fixed.dtype}"
        )

        # Verify values are preserved exactly as integers
        np.testing.assert_array_equal(raw_station_ids_fixed, station_ids)

        raw_ds_fixed.close()

        # and finally, testing that EFTS IO reads it correctly too
        eds_read = EftsDataSet(filename)
        station_ids_read = eds_read.data.coords[STATION_ID_DIMNAME].values
        assert np.issubdtype(station_ids_read.dtype, np.str_), (
            f"EftsDataSet read station_id dtype should be integer, got {station_ids_read.dtype}"
        )
        assert station_ids_read[0] == np.str_("123456789123")
        assert station_ids_read[1] == np.str_("987654321987")  # and NOT np.str_('987654321987.0')]

    finally:
        # Clean up temporary file
        if os.path.exists(filename):
            os.remove(filename)


def test_station_id_int32_preserved_on_read():
    """Test that int32 station_id values are also affected by the mask_and_scale issue.

    Tests with smaller station IDs that fit in int32 range to ensure the fix
    works for both i4 and i8 data types.
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import STATION_ID_VARNAME

    # Create test data with small int32 station IDs
    issue_times = pd.date_range("2023-01-01", periods=5, freq="D")
    station_ids = [123, 456, 789]  # Small values that fit in int32
    lead_times = np.arange(1, 3)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["station_X", "station_Y", "station_Z"],
        nc_attributes={
            "title": "Test dataset for int32 dtype preservation",
            "institution": "Test",
            "source": "Unit test",
            "catchment": "Test catchment",
            "comment": "Test for station_id int32 dtype preservation",
            "history": "Created for testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.stf2_int_datatype = "i4"  # Use int32 for small values

    # Add a data variable
    eds.create_data_variables(
        {
            "flow_obs": {
                "name": "flow_obs",
                "longname": "Streamflow",
                "units": "m^3/s",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    # populate some values for the data variable, a mix of missing values and real values
    eds.data["flow_obs"].loc[:, :, :, :] = np.random.rand(2, 3, 1, 5) * 100.0
    # Use actual coordinate values: lead_time=1, station_id=first station, all realisations, time=first time
    eds.data["flow_obs"].loc[1, station_ids[0], :, issue_times[0]] = np.nan  # introduce a missing value

    # Save to STF2 file
    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="flow_obs",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.OBSERVED,
        )

        # Read with default settings (reproduces the bug)
        raw_ds_with_bug = xr.open_dataset(filename, decode_times=False)
        raw_station_ids_buggy = raw_ds_with_bug[STATION_ID_VARNAME].values

        # Bug: converts to float64 even for int32 storage
        assert raw_station_ids_buggy.dtype == np.float64, (
            f"Bug not reproduced for int32! Expected float64, got {raw_station_ids_buggy.dtype}"
        )

        raw_ds_with_bug.close()

        # Read with fix
        raw_ds_fixed = xr.open_dataset(filename, decode_times=False, mask_and_scale=False)
        raw_station_ids_fixed = raw_ds_fixed[STATION_ID_VARNAME].values

        # With the fix, dtype should be int32
        assert np.issubdtype(raw_station_ids_fixed.dtype, np.integer), (
            f"Expected integer dtype with mask_and_scale=False, got {raw_station_ids_fixed.dtype}"
        )
        assert raw_station_ids_fixed.dtype == np.int32, (
            f"Expected int32 with mask_and_scale=False, got {raw_station_ids_fixed.dtype}"
        )

        # Verify values are preserved exactly
        np.testing.assert_array_equal(raw_station_ids_fixed, station_ids)

        raw_ds_fixed.close()

        # and finally, testing that EFTS IO reads it correctly too
        eds_read = EftsDataSet(filename)
        station_ids_read = eds_read.data.coords[STATION_ID_DIMNAME].values
        assert np.issubdtype(station_ids_read.dtype, np.str_), (
            f"EftsDataSet read station_id dtype should be integer, got {station_ids_read.dtype}"
        )
        assert station_ids_read[0] == np.str_("123")
        assert station_ids_read[1] == np.str_("456")

    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)


def test_save_to_stf2_preserves_data_array_attributes():
    """Test that save_to_stf2 correctly writes data array attributes to the NetCDF file.

    This test verifies that when a data variable is saved to STF2 format, the following
    attributes are preserved in the output NetCDF file:
    - UNITS_ATTR_KEY (compulsory)
    - LONG_NAME_ATTR_KEY
    - FILLVALUE_ATTR_KEY
    - TYPE_ATTR_KEY
    - TYPE_DESCRIPTION_ATTR_KEY
    - DAT_TYPE_ATTR_KEY
    - LOCATION_TYPE_ATTR_KEY
    """
    import tempfile
    import os
    import netCDF4 as nc
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import (
        UNITS_ATTR_KEY,
        LONG_NAME_ATTR_KEY,
        FILLVALUE_ATTR_KEY,
        TYPE_ATTR_KEY,
        TYPE_DESCRIPTION_ATTR_KEY,
        DAT_TYPE_ATTR_KEY,
        LOCATION_TYPE_ATTR_KEY,
    )

    # Create test dataset
    issue_times = pd.date_range("2023-01-01", periods=5, freq="D")
    station_ids = [100, 200]
    lead_times = np.arange(1, 4)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=2,
        station_names=["Station_A", "Station_B"],
        nc_attributes={
            "title": "Test dataset for attribute preservation",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Testing attribute preservation in save_to_stf2",
            "history": "Created for unit testing",
        },
    )

    eds = EftsDataSet(xr_ds)

    # Define custom attributes for the data variable
    custom_units = "mm/day"
    custom_long_name = "Custom rainfall variable"
    custom_fillvalue = -9999.0
    custom_type = 2
    custom_type_description = "accumulated over the preceding interval"
    custom_dat_type = "obs"
    custom_location_type = "Point"

    # Create data variable with custom attributes
    eds.create_data_variables(
        {
            "test_var": {
                "name": "test_var",
                "longname": custom_long_name,
                "units": custom_units,
                "dim_type": "4",
                "missval": custom_fillvalue,
                "precision": "double",
                "attributes": {
                    TYPE_ATTR_KEY: custom_type,
                    TYPE_DESCRIPTION_ATTR_KEY: custom_type_description,
                    DAT_TYPE_ATTR_KEY: custom_dat_type,
                    LOCATION_TYPE_ATTR_KEY: custom_location_type,
                },
            },
        }
    )

    # Check that the data variable has the correct attributes before saving
    data_var = eds.data["test_var"]
    assert data_var.attrs[UNITS_ATTR_KEY] == custom_units
    assert data_var.attrs[LONG_NAME_ATTR_KEY] == custom_long_name
    assert data_var.attrs[FILLVALUE_ATTR_KEY] == custom_fillvalue
    assert data_var.attrs[TYPE_ATTR_KEY] == custom_type
    assert data_var.attrs[TYPE_DESCRIPTION_ATTR_KEY] == custom_type_description
    assert data_var.attrs[DAT_TYPE_ATTR_KEY] == custom_dat_type
    assert data_var.attrs[LOCATION_TYPE_ATTR_KEY] == custom_location_type

    # Populate with test data
    eds.data["test_var"].loc[:, :, :, :] = np.random.rand(3, 2, 2, 5) * 10.0

    # Save to STF2 file
    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="test_var",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.OBSERVED,
        )

        # Read back the file with netCDF4 to check attributes
        nc_ds = nc.Dataset(filename, "r")

        # The variable name in the file follows STF conventions (e.g., "rain_obs")
        # Need to find which variable was created
        data_vars = [
            v
            for v in nc_ds.variables.keys()
            if not v.startswith(("time", "station", "lat", "lon", "lead_time", "ens_member", "area"))
        ]

        # Should be exactly one data variable
        assert len(data_vars) == 1, f"Expected 1 data variable, found {len(data_vars)}: {data_vars}"

        saved_var_name = data_vars[0]
        saved_var = nc_ds.variables[saved_var_name]

        # Verify compulsory attribute: UNITS_ATTR_KEY
        assert UNITS_ATTR_KEY in saved_var.ncattrs(), f"Missing compulsory attribute: {UNITS_ATTR_KEY}"
        assert saved_var.getncattr(UNITS_ATTR_KEY) == custom_units, (
            f"Expected units '{custom_units}', got '{saved_var.getncattr(UNITS_ATTR_KEY)}'"
        )

        # Verify LONG_NAME_ATTR_KEY
        assert LONG_NAME_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {LONG_NAME_ATTR_KEY}"
        assert saved_var.getncattr(LONG_NAME_ATTR_KEY) == custom_long_name, (
            f"Expected long_name '{custom_long_name}', got '{saved_var.getncattr(LONG_NAME_ATTR_KEY)}'"
        )

        # Verify FILLVALUE_ATTR_KEY
        assert FILLVALUE_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {FILLVALUE_ATTR_KEY}"
        assert saved_var.getncattr(FILLVALUE_ATTR_KEY) == custom_fillvalue, (
            f"Expected _FillValue {custom_fillvalue}, got {saved_var.getncattr(FILLVALUE_ATTR_KEY)}"
        )

        # Verify TYPE_ATTR_KEY
        assert TYPE_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {TYPE_ATTR_KEY}"
        assert saved_var.getncattr(TYPE_ATTR_KEY) == custom_type, (
            f"Expected type {custom_type}, got {saved_var.getncattr(TYPE_ATTR_KEY)}"
        )

        # Verify TYPE_DESCRIPTION_ATTR_KEY
        assert TYPE_DESCRIPTION_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {TYPE_DESCRIPTION_ATTR_KEY}"
        assert saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY) == custom_type_description, (
            f"Expected type_description '{custom_type_description}', got '{saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY)}'"
        )

        # Verify DAT_TYPE_ATTR_KEY
        assert DAT_TYPE_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {DAT_TYPE_ATTR_KEY}"
        assert saved_var.getncattr(DAT_TYPE_ATTR_KEY) == custom_dat_type, (
            f"Expected dat_type '{custom_dat_type}', got '{saved_var.getncattr(DAT_TYPE_ATTR_KEY)}'"
        )

        # Verify LOCATION_TYPE_ATTR_KEY
        assert LOCATION_TYPE_ATTR_KEY in saved_var.ncattrs(), f"Missing attribute: {LOCATION_TYPE_ATTR_KEY}"
        assert saved_var.getncattr(LOCATION_TYPE_ATTR_KEY) == custom_location_type, (
            f"Expected location_type '{custom_location_type}', got '{saved_var.getncattr(LOCATION_TYPE_ATTR_KEY)}'"
        )

        # ---- Convention compliance checks (structure, not just attributes) ----

        # Bug #1: Dimension order must match convention: (lead_time, station, ens_member, time)
        assert saved_var.dimensions == ("lead_time", "station", "ens_member", "time"), (
            f"Data variable dimension order should be (lead_time, station, ens_member, time) per STF 2.0, "
            f"got {saved_var.dimensions}"
        )

        # Bug #6: station_name dimensions must be (strLen, station) per convention
        stn_name_var = nc_ds.variables["station_name"]
        assert stn_name_var.dimensions == ("strLen", "station"), (
            f"station_name dimension order should be (strLen, station) per STF 2.0, "
            f"got {stn_name_var.dimensions}"
        )

        # Bug #7: Convention specifies data variables as double precision
        assert saved_var.dtype == np.float64, (
            f"Data variable should be float64 (double) per STF 2.0, got {saved_var.dtype}"
        )

        # Bug #5: lead_time axis attribute should be "u" per convention
        lt_var = nc_ds.variables["lead_time"]
        assert lt_var.getncattr("axis") == "u", (
            f"lead_time axis should be 'u' per STF 2.0, got '{lt_var.getncattr('axis')}'"
        )

        nc_ds.close()

    finally:
        # Clean up temporary file
        if os.path.exists(filename):
            os.remove(filename)


def test_stf2_default_attributes_match_conventions():
    """Test that default attributes written by write_nc_stf2 match STF 2.0 conventions.

    When no custom attributes are provided on the data variable (except the mandatory
    'units'), the function should derive correct defaults from the convention:
    - Bug #3: type_description for streamflow (type 3) should be "averaged over the preceding interval"
    - Bug #3: type_description for min temperature (type 5) should be "point value recorded in the preceding interval"
    - Bug #9: dat_type_description for OBSERVED should be "observed directly" (not "observed")
    - Bug #4: quality variable name suffix should be "_qul" (not "_qual")
    """
    import os
    import netCDF4 as nc
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import (
        UNITS_ATTR_KEY,
        TYPE_ATTR_KEY,
        TYPE_DESCRIPTION_ATTR_KEY,
        DAT_TYPE_ATTR_KEY,
        DAT_TYPE_DESCRIPTION_ATTR_KEY,
    )

    # Create test dataset
    issue_times = pd.date_range("2023-01-01", periods=5, freq="D")
    station_ids = [100, 200]
    lead_times = np.arange(1, 4)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=2,
        station_names=["Station_A", "Station_B"],
        nc_attributes={
            "title": "Test dataset for default attributes",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Testing convention-compliant defaults",
            "history": "Created for unit testing",
        },
    )

    eds = EftsDataSet(xr_ds)

    # Create data variable with ONLY the mandatory 'units' attribute — no custom overrides
    eds.create_data_variables(
        {
            "flow_var": {
                "name": "flow_var",
                "longname": "streamflow",
                "units": "m3/s",
                "dim_type": "4",
                "missval": -9999.0,
                "precision": "double",
                "attributes": {},  # No custom type/dat_type overrides
            },
        }
    )

    eds.data["flow_var"].loc[:, :, :, :] = np.random.rand(3, 2, 2, 5) * 10.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        # --- Test 1: STREAMFLOW + OBSERVED (default type_description and dat_type_description) ---
        eds.save_to_stf2(
            path=filename,
            variable_name="flow_var",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.OBSERVED,
        )

        nc_ds = nc.Dataset(filename, "r")

        # The written variable should be "q_obs" for streamflow + observed
        assert "q_obs" in nc_ds.variables, (
            f"Expected variable 'q_obs' in file, got variables: {list(nc_ds.variables.keys())}"
        )
        saved_var = nc_ds.variables["q_obs"]

        # Bug #3: Streamflow is type 3 = "averaged over the preceding interval"
        assert saved_var.getncattr(TYPE_ATTR_KEY) == 3, (
            f"Streamflow default type should be 3, got {saved_var.getncattr(TYPE_ATTR_KEY)}"
        )
        assert saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY) == "averaged over the preceding interval", (
            f"Streamflow default type_description should be 'averaged over the preceding interval', "
            f"got '{saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY)}'"
        )

        # Bug #9: dat_type_description for OBSERVED should be "observed directly"
        assert saved_var.getncattr(DAT_TYPE_ATTR_KEY) == "obs", (
            f"Expected dat_type 'obs', got '{saved_var.getncattr(DAT_TYPE_ATTR_KEY)}'"
        )
        assert saved_var.getncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY) == "observed directly", (
            f"Expected dat_type_description 'observed directly', "
            f"got '{saved_var.getncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY)}'"
        )

        nc_ds.close()

        # --- Test 2: MINIMUM_TEMPERATURE + OBSERVED (type 5 default) ---
        if os.path.exists(filename):
            os.remove(filename)

        eds.save_to_stf2(
            path=filename,
            variable_name="flow_var",
            var_type=StfVariable.MINIMUM_TEMPERATURE,
            data_type=DataOriginType.OBSERVED,
        )

        nc_ds = nc.Dataset(filename, "r")

        assert "tmin_obs" in nc_ds.variables, (
            f"Expected variable 'tmin_obs' in file, got variables: {list(nc_ds.variables.keys())}"
        )
        saved_var = nc_ds.variables["tmin_obs"]

        # Bug #3: Min temperature is type 5 = "point value recorded in the preceding interval"
        assert saved_var.getncattr(TYPE_ATTR_KEY) == 5, (
            f"Min temperature default type should be 5, got {saved_var.getncattr(TYPE_ATTR_KEY)}"
        )
        assert saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY) == "point value recorded in the preceding interval", (
            f"Min temperature default type_description should be 'point value recorded in the preceding interval', "
            f"got '{saved_var.getncattr(TYPE_DESCRIPTION_ATTR_KEY)}'"
        )

        nc_ds.close()

        # --- Test 3: STREAMFLOW + FORECAST (dat_type_description default) ---
        if os.path.exists(filename):
            os.remove(filename)

        eds.save_to_stf2(
            path=filename,
            variable_name="flow_var",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.FORECAST,
        )

        nc_ds = nc.Dataset(filename, "r")

        assert "q_sim" in nc_ds.variables, (
            f"Expected variable 'q_sim' in file, got variables: {list(nc_ds.variables.keys())}"
        )
        saved_var = nc_ds.variables["q_sim"]

        # Bug #9: dat_type_description for FORECAST should be "simulated from forecasts"
        assert saved_var.getncattr(DAT_TYPE_ATTR_KEY) == "fct", (
            f"Expected dat_type 'fct', got '{saved_var.getncattr(DAT_TYPE_ATTR_KEY)}'"
        )
        assert saved_var.getncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY) == "simulated from forecasts", (
            f"Expected dat_type_description 'simulated from forecasts', "
            f"got '{saved_var.getncattr(DAT_TYPE_DESCRIPTION_ATTR_KEY)}'"
        )

        nc_ds.close()

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_quality_variable_name_suffix_matches_convention():
    """Test that quality variable name uses '_qul' suffix per STF 2.0.

    Bug #4: The convention names quality variables as e.g. 'rain_obs_qul',
    but the code currently writes 'rain_obs_qual'.
    """
    import os
    import netCDF4 as nc
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable

    issue_times = pd.date_range("2023-01-01", periods=5, freq="D")
    station_ids = [100, 200]
    lead_times = np.arange(1, 4)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=2,
        station_names=["Station_A", "Station_B"],
        nc_attributes={
            "title": "Test quality variable naming",
            "institution": "Test Institution",
            "source": "Unit test",
            "catchment": "Test_Catchment",
            "comment": "Testing quality variable suffix",
            "history": "Created for unit testing",
        },
    )

    eds = EftsDataSet(xr_ds)

    eds.create_data_variables(
        {
            "rain_var": {
                "name": "rain_var",
                "longname": "rainfall",
                "units": "mm",
                "dim_type": "4",
                "missval": -9999.0,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    eds.data["rain_var"].loc[:, :, :, :] = np.random.rand(3, 2, 2, 5) * 10.0

    # Create a quality data array with the same shape
    qual_data = xr.DataArray(
        np.ones_like(eds.data["rain_var"].values, dtype=np.float32),
        dims=eds.data["rain_var"].dims,
        coords=eds.data["rain_var"].coords,
        attrs={"quality_code": "BOM Quality codes"},
    )

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_var",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.OBSERVED,
            data_qual=qual_data,
        )

        nc_ds = nc.Dataset(filename, "r")

        # Convention says quality variables are named e.g. "rain_obs_qul"
        all_vars = list(nc_ds.variables.keys())
        assert "rain_obs_qul" in all_vars, (
            f"Expected quality variable 'rain_obs_qul' per STF 2.0 convention, "
            f"found variables: {all_vars}"
        )

        nc_ds.close()

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def _verify_time_attributes_preservation(timezone_str: str):
    """Helper function to test that time coordinate attributes and timezone are preserved when writing to STF2.

    Args:
        timezone_str: Timezone string (e.g., "UTC", "US/Eastern", "Australia/Sydney")

    This function verifies:
    1. In-memory xarray dataset with specified timezone timestamps can be saved
    2. The time_standard attribute is written correctly
    3. The time units string includes proper timezone offset
    4. Time values remain consistent when read back
    """
    import tempfile
    import os
    import netCDF4 as nc
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import TIME_STANDARD_ATTR_KEY, UNITS_ATTR_KEY

    # Create test dataset with explicit timezone timestamps
    # Using daily timesteps with distinct dates
    try:
        issue_times = pd.date_range("2024-01-15", periods=7, freq="D", tz=timezone_str)
    except pytz.exceptions.UnknownTimeZoneError as e:
        # the error message is not overly terse, so warpping this.
        raise ValueError(f"Unknown timezone string '{timezone_str}'")
    station_ids = [1001, 2002]
    lead_times = np.arange(1, 4)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="days",
        ensemble_size=1,
        station_names=["Site_Alpha", "Site_Beta"],
        nc_attributes={
            "title": f"Test dataset for {timezone_str} timezone preservation",
            "institution": "Test Lab",
            "source": "Unit test",
            "catchment": "Test Basin",
            "comment": f"Testing {timezone_str} timezone in time attributes",
            "history": "Created for timezone testing",
        },
    )

    # Verify the input dataset has the specified timezone
    first_time = xr_ds.time.values[0]
    assert isinstance(first_time, pd.Timestamp), f"Expected time coordinate to be Timestamp, got {type(first_time)}"

    eds = EftsDataSet(xr_ds)

    # Create a simple data variable
    eds.create_data_variables(
        {
            "temp_obs": {
                "name": "temp_obs",
                "longname": "Temperature",
                "units": "degC",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    # Populate with test data
    eds.data["temp_obs"].loc[:, :, :, :] = np.random.rand(3, 2, 1, 7) * 20.0 + 10.0

    # Save to STF2 file
    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="temp_obs",
            var_type=StfVariable.MAXIMUM_TEMPERATURE,
            data_type=DataOriginType.OBSERVED,
            timestep="days",
        )

        # Read back with netCDF4 to check time attributes
        nc_ds = nc.Dataset(filename, "r")

        time_var = nc_ds.variables["time"]

        # Verify time_standard attribute exists
        assert TIME_STANDARD_ATTR_KEY in time_var.ncattrs(), (
            f"Missing {TIME_STANDARD_ATTR_KEY} attribute on time variable"
        )
        time_standard = time_var.getncattr(TIME_STANDARD_ATTR_KEY)
        assert "UTC" in time_standard, f"Expected UTC in time_standard attribute, got '{time_standard}'"

        # Verify time units string contains timezone offset
        assert UNITS_ATTR_KEY in time_var.ncattrs(), f"Missing {UNITS_ATTR_KEY} attribute on time variable"
        time_units = time_var.getncattr(UNITS_ATTR_KEY)
        # Check for timezone offset in the units string (e.g., +0000, +00:00, +1000, +10:00)
        assert any(tz_marker in time_units for tz_marker in ["+", "-"]), (
            f"Expected timezone offset in time units, got '{time_units}'"
        )

        # Verify the time units follow expected format (e.g., "days since YYYY-MM-DD HH:MM:SS +0000")
        assert time_units.startswith("days since"), (
            f"Expected time units to start with 'days since', got '{time_units}'"
        )

        # Read time values and verify they are integers (encoded as offset from origin)
        time_values = time_var[:]
        assert len(time_values) == 7, f"Expected 7 time values, got {len(time_values)}"
        assert np.issubdtype(time_values.dtype, np.integer), f"Expected integer time values, got {time_values.dtype}"

        # Verify time values are sequential (daily step = 1 day offset)
        time_diffs = np.diff(time_values)
        assert np.all(time_diffs == 1), f"Expected daily increments of 1, got {time_diffs}"

        # Bug #5: lead_time axis attribute should be "u" per STF 2.0 convention
        lt_var = nc_ds.variables["lead_time"]
        assert lt_var.getncattr("axis") == "u", (
            f"lead_time axis should be 'u' per STF 2.0, got '{lt_var.getncattr('axis')}'"
        )

        nc_ds.close()

        # Also verify that EftsDataSet can read it back correctly
        eds_read = EftsDataSet(filename)
        time_coords_read = eds_read.data.time.values

        # Check we got the same number of timesteps
        assert len(time_coords_read) == 7, f"Expected 7 time coordinates after reading, got {len(time_coords_read)}"

        # Verify time coordinate values are datetime-like
        assert hasattr(time_coords_read[0], "year"), "Time coordinates should be datetime-like objects"

        # Verify that the time axis matches exactly what was saved
        # Convert both to pandas Timestamps for comparison (handling timezone differences)
        original_times = pd.to_datetime(issue_times)
        read_back_times = pd.to_datetime(time_coords_read)

        # # Convert to UTC for comparison if needed (normalize timezone info)
        # if original_times.tz is not None:
        #     original_times = original_times.tz_convert("UTC")
        # if read_back_times.tz is not None:
        #     read_back_times = read_back_times.tz_convert("UTC")
        # else:
        #     # If read_back is timezone-naive, localize to UTC for comparison
        #     read_back_times = read_back_times.tz_localize("UTC")

        # time zones are identical in utc offset.
        # Relaxing the condition to offsets not tz equality to allow for 'Etc/UTC and Etc/GMT'
        assert original_times[0].utcoffset() == read_back_times[0].utcoffset(), (
            f"Timezone mismatch: original={original_times[0].tz}, read_back={read_back_times[0].tz}"
        )

        # Check that all timestamps match exactly
        for i, (orig, read) in enumerate(zip(original_times, read_back_times)):
            assert orig == read, f"Time coordinate mismatch at index {i}: original={orig}, read_back={read}"

    finally:
        # Clean up temporary file
        if os.path.exists(filename):
            os.remove(filename)


def test_time_attributes_and_utc_timezone_preserved():
    """Test that time coordinate attributes and UTC timezone are preserved when writing to STF2.

    This test verifies that timestamps in UTC timezone are correctly preserved through
    the save/load cycle to STF2 format.
    """
    _verify_time_attributes_preservation("UTC")


def test_time_attributes_and_utc_plus1_timezone_preserved():
    """Test that time coordinate attributes and UTC+01:00 timezone are preserved when writing to STF2."""
    _verify_time_attributes_preservation("UTC+01:00")


def test_time_attributes_and_utc_minus1_timezone_preserved():
    """Test that time coordinate attributes and UTC-01:00 timezone are preserved when writing to STF2."""
    _verify_time_attributes_preservation("UTC-01:00")


def test_time_attributes_and_sydney_timezone_preserved():
    """Test that writing EFTS data with daylight saving timezone raises an exception.

    This test verifies that attempting to save data with a timezone that observes daylight
    saving time (like Australia/Sydney) raises an appropriate exception. This is part of
    test-driven development - the feature to handle DST has not yet been implemented.

    Background: The timezone offset can vary depending on whether daylight saving time is
    in effect, which complicates the time encoding in NetCDF files.
    """
    with pytest.raises((ValueError, NotImplementedError)) as exc_info:
        _verify_time_attributes_preservation("Australia/Sydney")

    # Verify the exception message mentions daylight saving or timezone
    error_msg = str(exc_info.value).lower()
    assert any(keyword in error_msg for keyword in ["daylight", "dst", "timezone", "time zone"]), (
        f"Expected exception message to mention daylight saving or timezone issues, got: {exc_info.value}"
    )


# ============================================================================
# Comprehensive Timezone Test Suite
# ============================================================================
# This section provides systematic test coverage for timezone handling in STF2
# file I/O operations. Tests are organized into groups by timezone category.
# ============================================================================

# Timezone test constants - organized by category
FIXED_OFFSET_POSITIVE = [
    "UTC+05:00",
    "UTC+05:30",  # India - non-hour offset
    "UTC+05:45",  # Nepal - 45-minute offset
    "UTC+09:00",
    "UTC+09:30",  # Australia/Adelaide - non-hour offset
    "UTC+10:00",
    "UTC+11:00",
    "UTC+14:00",  # Line Islands - edge case (maximum offset)
]

FIXED_OFFSET_NEGATIVE = [
    "UTC-02:00",
    "UTC-10:00",
    "UTC-12:00",  # Baker Island - edge case (minimum offset)
]

FIXED_OFFSET_SHORT_HOUR = [
    "UTC+1",
    "UTC-10",
]

UTC_ALIASES = [
    "UTC",
    "GMT",
    "Etc/UTC",
]

UNSUPPORTED_OFFSETS = [
    "GMT+01:00",
    "Etc/GMT-01:00",
    "Etc/UTC+10:00",
]

DST_TIMEZONES = [
    "US/Eastern",
    "US/Pacific",
    "US/Mountain",
    "Europe/Paris",
    "Europe/Berlin",
    "Australia/Sydney",
    "Australia/Melbourne",
    "America/Los_Angeles",
]


@pytest.mark.parametrize("timezone_str", FIXED_OFFSET_POSITIVE + FIXED_OFFSET_NEGATIVE)
def test_fixed_offset_timezones_preserved(timezone_str):
    """Test that fixed UTC offset timezones are correctly preserved through save/load cycle.

    This test verifies that timezones with fixed offsets (no DST) are handled correctly:
    - Positive offsets (UTC+HH:MM)
    - Negative offsets (UTC-HH:MM)
    - Non-hour offsets (e.g., UTC+05:30, UTC+05:45, UTC+09:30)
    - Edge cases (UTC+14:00, UTC-12:00)

    All these should work with the current implementation since they have constant offsets.
    """
    _verify_time_attributes_preservation(timezone_str)


@pytest.mark.parametrize("timezone_str", UTC_ALIASES)
def test_utc_alias_timezones_preserved(timezone_str):
    """Test that UTC alias timezones produce equivalent results.

    This test verifies that different representations of UTC (UTC, GMT, Etc/UTC)
    all produce identical behavior when saving and loading STF2 files.
    """
    _verify_time_attributes_preservation(timezone_str)


@pytest.mark.parametrize("timezone_str", DST_TIMEZONES)
def test_dst_timezones_raise_appropriate_error(timezone_str):
    """Test that DST timezones fail with descriptive error messages.

    This test documents expected behavior for timezones that observe daylight saving time.
    These timezones have variable offsets depending on the date, which is incompatible
    with NetCDF's static "time since ORIGIN +OFFSET" encoding format.

    Expected behavior: Raise ValueError or NotImplementedError with a message mentioning
    "daylight", "dst", or "timezone".
    """
    with pytest.raises((ValueError, NotImplementedError)) as exc_info:
        _verify_time_attributes_preservation(timezone_str)

    # Verify the exception message is descriptive
    error_msg = str(exc_info.value).lower()
    assert any(keyword in error_msg for keyword in ["daylight", "dst", "timezone", "time zone"]), (
        f"Expected exception message to mention daylight saving or timezone issues, got: {exc_info.value}"
    )


@pytest.mark.parametrize("timezone_str", UNSUPPORTED_OFFSETS)
def test_unsupported_offset_formats_raise_appropriate_error(timezone_str):
    """Test that unsupported timezone offset formats fail with descriptive error messages.

    This test documents expected behavior for timezone strings that use unsupported formats
    such as "GMT+01:00", "Etc/GMT-01:00", or "Etc/UTC+10:00". These formats are not
    supported by the current implementation.

    Expected behavior: Raise an exception.
    """
    # NOTE: actually raised in test helper , so not of great value, but may be if code is refactored.
    with pytest.raises((ValueError,)) as exc_info:
        _verify_time_attributes_preservation(timezone_str)

    # # Verify the exception message is descriptive
    # error_msg = str(exc_info.value).lower()
    # assert any(keyword in error_msg for keyword in ["offset", "format", "unsupported", "timezone", "time zone"]), (
    #     f"Expected exception message to mention offset, format, or unsupported timezone issues, got: {exc_info.value}"
    # )


@pytest.mark.parametrize("timezone_str", FIXED_OFFSET_SHORT_HOUR)
def test_short_hour_offset_timezones_preserved(timezone_str):
    """Test that short-form hour offset timezones are not supported

    This test verifies that timezones with short-form hour offsets (e.g., "UTC+1", "UTC-10")
    are rejected.
    """
    # NOTE: actually raised in test helper because of pytz , so not of great value, but may be if code is refactored.
    with pytest.raises((ValueError,)) as exc_info:
        _verify_time_attributes_preservation(timezone_str)


def test_timezone_naive_timestamps_localized_to_utc():
    """Test that timezone-naive timestamps are interpreted as UTC.

    This test verifies the default behavior when creating datasets with timezone-naive
    pandas timestamps. The expected behavior is that they are localized to UTC.
    """
    import tempfile
    import os
    import netCDF4 as nc
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable
    from efts_io.conventions import TIME_STANDARD_ATTR_KEY, UNITS_ATTR_KEY

    # Create test dataset with timezone-naive timestamps (no tz parameter)
    issue_times = pd.date_range("2024-02-15", periods=5, freq="D")  # No tz - naive
    station_ids = [301, 302]
    lead_times = np.arange(1, 4)

    # Verify timestamps are indeed timezone-naive
    assert issue_times.tz is None, "Test setup error: timestamps should be timezone-naive"

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="days",
        ensemble_size=1,
        station_names=["Site_Gamma", "Site_Delta"],
        nc_attributes={
            "title": "Test dataset for timezone-naive timestamps",
            "institution": "Test Lab",
            "source": "Unit test",
            "catchment": "Test Basin",
            "comment": "Testing timezone-naive timestamp handling",
            "history": "Created for timezone-naive testing",
        },
    )

    eds = EftsDataSet(xr_ds)

    eds.create_data_variables(
        {
            "precip_obs": {
                "name": "precip_obs",
                "longname": "Precipitation",
                "units": "mm",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    eds.data["precip_obs"].loc[:, :, :, :] = np.random.rand(3, 2, 1, 5) * 25.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="precip_obs",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.OBSERVED,
            timestep="days",
        )

        # Read back and verify UTC is assumed
        nc_ds = nc.Dataset(filename, "r")
        time_var = nc_ds.variables["time"]

        time_standard = time_var.getncattr(TIME_STANDARD_ATTR_KEY)
        assert "UTC" in time_standard, f"Expected UTC in time_standard, got '{time_standard}'"

        time_units = time_var.getncattr(UNITS_ATTR_KEY)
        # Should contain +00:00 or +0000 indicating UTC
        assert "+00" in time_units or "+0000" in time_units, f"Expected UTC offset in time units, got '{time_units}'"

        nc_ds.close()

        # Verify EftsDataSet can read it back
        eds_read = EftsDataSet(filename)
        time_coords = eds_read.data.time.values

        assert len(time_coords) == 5, f"Expected 5 time coordinates, got {len(time_coords)}"

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_invalid_timezone_string_raises_error():
    """Test that invalid timezone strings raise appropriate errors.

    This test verifies error handling for malformed or non-existent timezone strings.
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable

    invalid_timezones = [
        "Invalid/Timezone",
        "NotAPlace/NotACity",
        "UTC+99:99",  # Malformed offset
        "GMT+25",  # Out of range
    ]

    for invalid_tz in invalid_timezones:
        # Create dataset with invalid timezone - this should fail during dataset creation
        # or during save_to_stf2 operation
        try:
            issue_times = pd.date_range("2024-03-01", periods=3, freq="D", tz=invalid_tz)
            # If we get here, pandas accepted it (shouldn't happen for truly invalid TZ)
            # but it should still fail during save

            xr_ds = xr_efts(
                issue_times=issue_times,
                station_ids=[501],
                lead_times=[1, 2],
                lead_time_tstep="hours",
                ensemble_size=1,
                station_names=["Test_Station"],
                nc_attributes={
                    "title": "Test",
                    "institution": "Test",
                    "source": "Test",
                    "catchment": "Test",
                    "comment": "Test",
                    "history": "Test",
                },
            )

            eds = EftsDataSet(xr_ds)
            eds.create_data_variables(
                {
                    "test_var": {
                        "name": "test_var",
                        "longname": "Test",
                        "units": "mm",
                        "dim_type": "4",
                        "missval": np.nan,
                        "precision": "double",
                        "attributes": {},
                    },
                }
            )
            eds.data["test_var"].loc[:, :, :, :] = 1.0

            with _temporary_named_file() as tmp:
                filename = tmp.name

            try:
                with pytest.raises((ValueError, KeyError, Exception)):
                    eds.save_to_stf2(
                        path=filename,
                        variable_name="test_var",
                        var_type=StfVariable.RAINFALL,
                        data_type=DataOriginType.OBSERVED,
                    )
            finally:
                if os.path.exists(filename):
                    os.remove(filename)

        except (ValueError, KeyError, Exception):
            # Expected - pandas or pytz rejected the timezone string during date_range creation
            pass


def test_extreme_valid_offsets_preserved():
    """Test that extreme but valid UTC offsets are correctly handled.

    This test verifies the edge cases of the valid timezone offset range:
    - UTC+14:00 (Line Islands, Kiribati) - maximum valid offset
    - UTC-12:00 (Baker Island, Howland Island) - minimum valid offset
    """
    extreme_offsets = ["UTC+14:00", "UTC-12:00"]

    for offset in extreme_offsets:
        _verify_time_attributes_preservation(offset)


def test_roundtrip_precision_with_hourly_timestep():
    """Test timestamp precision preservation with hourly timestep.

    This test verifies that timestamps are exactly preserved through the save/load
    cycle when using hourly timestep (not just daily).
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable

    # Create hourly timestamps
    issue_times = pd.date_range("2024-04-10 00:00", periods=24, freq="h", tz="UTC+05:00")
    station_ids = [601]
    lead_times = np.arange(1, 3)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=1,
        station_names=["Hourly_Station"],
        nc_attributes={
            "title": "Hourly timestep test",
            "institution": "Test",
            "source": "Unit test",
            "catchment": "Test",
            "comment": "Testing hourly precision",
            "history": "Created for hourly timestep testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "flow_hourly": {
                "name": "flow_hourly",
                "longname": "Hourly Flow",
                "units": "m^3/s",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    eds.data["flow_hourly"].loc[:, :, :, :] = np.random.rand(2, 1, 1, 24) * 50.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="flow_hourly",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.OBSERVED,
            timestep="hours",
        )

        # Read back and verify timestamps
        eds_read = EftsDataSet(filename)
        time_coords_read = eds_read.data.time.values

        assert len(time_coords_read) == 24, f"Expected 24 hourly timestamps, got {len(time_coords_read)}"

        # Convert to pandas for comparison
        original_times = pd.to_datetime(issue_times)
        read_back_times = pd.to_datetime(time_coords_read)

        # Verify each timestamp matches
        for i, (orig, read) in enumerate(zip(original_times, read_back_times)):
            assert orig == read, f"Timestamp mismatch at index {i}: original={orig}, read_back={read}"

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_roundtrip_precision_with_minute_timestep():
    """Test timestamp precision preservation with minute timestep.

    This test verifies that timestamps are exactly preserved with even finer
    temporal resolution (minutes).
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts
    from efts_io._ncdf_stf2 import StfVariable

    # Create minute-resolution timestamps
    issue_times = pd.date_range("2024-05-15 12:00", periods=60, freq="min", tz="UTC-07:00")
    station_ids = [701]
    lead_times = np.arange(1, 3)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="minutes",
        ensemble_size=1,
        station_names=["Minute_Station"],
        nc_attributes={
            "title": "Minute timestep test",
            "institution": "Test",
            "source": "Unit test",
            "catchment": "Test",
            "comment": "Testing minute precision",
            "history": "Created for minute timestep testing",
        },
    )

    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "level_minute": {
                "name": "level_minute",
                "longname": "Water Level (minute resolution)",
                "units": "m",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    eds.data["level_minute"].loc[:, :, :, :] = np.random.rand(2, 1, 1, 60) * 10.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="level_minute",
            var_type=StfVariable.STREAMFLOW,  # hack of sorts.
            data_type=DataOriginType.OBSERVED,
            timestep="minutes",
        )

        # Read back and verify timestamps
        eds_read = EftsDataSet(filename)
        time_coords_read = eds_read.data.time.values

        assert len(time_coords_read) == 60, f"Expected 60 minute timestamps, got {len(time_coords_read)}"

        # Convert to pandas for comparison
        original_times = pd.to_datetime(issue_times)
        read_back_times = pd.to_datetime(time_coords_read)

        # Verify minute-level precision
        for i, (orig, read) in enumerate(zip(original_times, read_back_times)):
            assert orig == read, f"Timestamp mismatch at minute {i}: original={orig}, read_back={read}"

    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_single_station_single_ensemble_single_leadtime():
    """Test that files with single-element dimensions load correctly.

    Reproduces an issue where 0-dimensional arrays (scalars) were returned
    when there was only one station/ensemble/lead_time, causing xarray coordinate
    creation to fail with: "dimensions must have the same length as the number
    of data dimensions, ndim=0".

    The fix uses np.atleast_1d() to ensure coordinate arrays are always 1D.
    """
    import tempfile
    import os
    from efts_io.wrapper import EftsDataSet, xr_efts, load_from_stf2_file
    from efts_io._ncdf_stf2 import StfVariable

    # Create test data with single station, single ensemble, single lead time
    issue_times = pd.date_range("2023-06-01", periods=10, freq="D")
    station_ids = ["17"]  # Single station - this triggers the bug
    lead_times = [1]  # Single lead time
    ensemble_size = 1  # Single ensemble member

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=ensemble_size,
        station_names=["Single Station"],
        nc_attributes={
            "title": "Test dataset for single-element dimensions",
            "institution": "Test",
            "source": "Unit test",
            "catchment": "Test catchment",
            "comment": "Testing single station/ensemble/lead_time",
            "history": "Created for testing",
        },
    )

    eds = EftsDataSet(xr_ds)

    # Add a data variable
    eds.create_data_variables(
        {
            "flow_obs": {
                "name": "flow_obs",
                "longname": "Observed streamflow",
                "units": "m^3/s",
                "dim_type": "4",
                "missval": np.nan,
                "precision": "double",
                "attributes": {},
            },
        }
    )

    # Populate with test data - shape is (lead_time, station, realisation, time)
    eds.data["flow_obs"].loc[:, :, :, :] = np.random.rand(1, 1, 1, 10) * 50.0

    # Save to STF2 file
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="flow_obs",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.OBSERVED,
        )

        # This is where the bug would occur - loading a file with single-element dimensions
        loaded_ds = load_from_stf2_file(filename, time_zone_timestamps=True)

        # Verify dimensions are correct
        assert STATION_ID_DIMNAME in loaded_ds.dims
        assert REALISATION_DIMNAME in loaded_ds.dims
        assert LEAD_TIME_DIMNAME in loaded_ds.dims
        assert TIME_DIMNAME in loaded_ds.dims

        # Verify dimension sizes
        assert loaded_ds.sizes[STATION_ID_DIMNAME] == 1
        assert loaded_ds.sizes[REALISATION_DIMNAME] == 1
        assert loaded_ds.sizes[LEAD_TIME_DIMNAME] == 1
        assert loaded_ds.sizes[TIME_DIMNAME] == 10

        # Verify station_id coordinate is correct
        station_ids_loaded = loaded_ds.coords[STATION_ID_DIMNAME].values
        assert len(station_ids_loaded) == 1
        assert station_ids_loaded[0] == "17"

        # Also test via EftsDataSet constructor
        eds_read = EftsDataSet(filename)
        assert eds_read.data.sizes[STATION_ID_DIMNAME] == 1
        assert eds_read.data.coords[STATION_ID_DIMNAME].values[0] == "17"

    finally:
        if os.path.exists(filename):
            os.remove(filename)
