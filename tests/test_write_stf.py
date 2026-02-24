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
    from efts_io._ncdf_stf2 import StfVariable, StfDataType
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
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="test_var",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.OBSERVED,
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

        nc_ds.close()

    finally:
        # Clean up temporary file
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
    from efts_io._ncdf_stf2 import StfVariable, StfDataType
    from efts_io.conventions import TIME_STANDARD_ATTR_KEY, UNITS_ATTR_KEY

    # Create test dataset with explicit timezone timestamps
    # Using daily timesteps with distinct dates
    issue_times = pd.date_range("2024-01-15", periods=7, freq="D", tz=timezone_str)
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
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="temp_obs",
            var_type=StfVariable.MAXIMUM_TEMPERATURE,
            data_type=StfDataType.OBSERVED,
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

        # Convert to UTC for comparison if needed (normalize timezone info)
        if original_times.tz is not None:
            original_times = original_times.tz_convert("UTC")
        if read_back_times.tz is not None:
            read_back_times = read_back_times.tz_convert("UTC")
        else:
            # If read_back is timezone-naive, localize to UTC for comparison
            read_back_times = read_back_times.tz_localize("UTC")

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


def test_time_attributes_and_sydney_timezone_preserved():
    """Test that time coordinate attributes and Australia/Sydney timezone are preserved when writing to STF2.

    This test verifies that timestamps in Australian Eastern Standard Time (Sydney) are correctly
    preserved through the save/load cycle to STF2 format. The timezone offset will vary depending
    on whether daylight saving time is in effect.
    """
    _verify_time_attributes_preservation("Australia/Sydney")


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
    from efts_io._ncdf_stf2 import StfVariable, StfDataType

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
            data_type=StfDataType.OBSERVED,
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
