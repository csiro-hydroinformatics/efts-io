from datetime import datetime
import pytest
import pandas as pd
import xarray as xr
import numpy as np
from efts_io._ncdf_stf2 import _create_cf_time_axis
from efts_io.conventions import convert_to_datetime64_utc


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
    assert calendar == "proleptic_gregorian"


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
    with pytest.raises(
        TypeError,
        match="Expected data\\[TIME_DIMNAME\\] to be of a type convertible to pd.Timestamp, got <class 'numpy.int64'> instead.",
    ):
        _create_cf_time_axis(data, "days")


# Unit tests
def test_convert_to_datetime64_utc():
    # Test with a timezone-naive pd.Timestamp
    naive_timestamp = pd.Timestamp("2023-10-01 12:00:00")
    assert convert_to_datetime64_utc(naive_timestamp) == np.datetime64("2023-10-01T12:00:00.000000000")

    # Test with a timezone-aware pd.Timestamp
    aware_timestamp = pd.Timestamp("2023-10-01 12:00:00", tz="America/New_York")
    assert convert_to_datetime64_utc(aware_timestamp) == np.datetime64("2023-10-01T16:00:00.000000000")

    # Test with a timezone-naive datetime
    naive_datetime = datetime(2023, 10, 1, 12, 0, 0)
    assert convert_to_datetime64_utc(naive_datetime) == np.datetime64("2023-10-01T12:00:00.000000000")

    # Test with a timezone-aware datetime
    from zoneinfo import ZoneInfo

    utc_tz = ZoneInfo("UTC")
    aware_datetime = datetime(2023, 10, 1, 12, 0, 0, tzinfo=utc_tz)
    assert convert_to_datetime64_utc(aware_datetime) == np.datetime64("2023-10-01T12:00:00.000000000")

    # Test with a string representation
    naive_string = "2023-10-01 12:00:00"
    assert convert_to_datetime64_utc(naive_string) == np.datetime64("2023-10-01T12:00:00.000000000")

    # Test with a timezone-aware string representation
    aware_string = "2023-10-01 12:00:00-04:00"
    assert convert_to_datetime64_utc(aware_string) == np.datetime64("2023-10-01T16:00:00.000000000")

    # Test with an np.datetime64
    naive_np_datetime = np.datetime64("2023-10-01T12:00:00.000000000")
    assert convert_to_datetime64_utc(naive_np_datetime) == np.datetime64("2023-10-01T12:00:00.000000000")


if __name__ == "__main__":
    test_create_cf_time_axis_invalid_time_type()
    test_create_cf_time_axis_empty_data()
    test_create_cf_time_axis_valid_input()
