from typing import Iterable
import pytest
import numpy as np
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
    xr_to_stf_dims,
    stf_to_xr_dims,
)


def sample_dataset(
    n_time=5,
    n_stations=2,
    n_lead_time=3,
    n_realisations=4,
):
    """Create a sample dataset with all required coordinates."""
    stations_nbs = np.arange(n_stations)
    ds = xr.Dataset(
        coords={
            TIME_DIMNAME: pd.date_range("2023-01-01", periods=n_time),
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


def create_valid_stf2_dataset():
    """Create a dataset with all required dimensions, variables, and attributes for STF 2.0."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)

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
    from efts_io._ncdf_stf2 import StfVariable, StfDataType
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
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.OBSERVED,
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
    from efts_io._ncdf_stf2 import StfVariable, StfDataType
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
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="flow_obs",
            var_type=StfVariable.STREAMFLOW,
            data_type=StfDataType.OBSERVED,
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
