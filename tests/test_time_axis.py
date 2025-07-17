import pytest
import pandas as pd
import xarray as xr
import numpy as np
from efts_io._ncdf_stf2 import _create_cf_time_axis

def test_create_cf_time_axis_valid_input():
    # Create a sample DataArray with a time dimension
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    data = xr.DataArray(np.random.rand(5), dims=["time"], coords={"time": dates})

    # Test with a valid time step
    result, units, calendar = _create_cf_time_axis(data, "days")

    # Check if the result is a numpy array
    assert isinstance(result, np.ndarray)
    assert len(result) == 5
    assert units == "days since 2023-01-01 00:00:00+00:00"
    assert calendar is None

def test_create_cf_time_axis_empty_data():
    # Create an empty DataArray
    data = xr.DataArray([], dims=["time"])

    # Test with an empty DataArray
    with pytest.raises(ValueError, match="Cannot create CF time axis from empty data array."):
        _create_cf_time_axis(data, "days")

def test_create_cf_time_axis_invalid_time_type():
    # Create a DataArray with invalid time type
    data = xr.DataArray([1, 2, 3], dims=["time"], coords={"time": [1, 2, 3]})

    # Test with invalid time type
    with pytest.raises(TypeError, match="Expected data\\[TIME_DIMNAME\\] to be of type pd.Timestamp, got <class 'numpy.int64'> instead."):
        _create_cf_time_axis(data, "days")

if __name__ == "__main__":
    test_create_cf_time_axis_invalid_time_type()
    test_create_cf_time_axis_empty_data()
    test_create_cf_time_axis_valid_input()
