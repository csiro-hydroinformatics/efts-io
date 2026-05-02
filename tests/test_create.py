# import netCDF4
import os

import numpy as np
import pandas as pd
import pytest

from efts_io._ncdf_stf2 import StfVariable
from efts_io.attributes import template_variable_attributes
from efts_io.conventions import DataOriginType
from efts_io.wrapper import EftsDataSet, xr_efts
from tests.test_write_stf import _temporary_named_file


def test_create_new_efts_stf2():
    """Placeholder test, for upcoming version of the conventions.

    Note the use of integers for station IDs, not strings.
    """
    import efts_io.wrapper as wrap

    issue_times = pd.date_range("2010-01-01", periods=31, freq="D")
    station_ids = [123, 456]
    lead_times = np.arange(start=1, stop=4, step=1)
    lead_time_tstep = "hours"
    ensemble_size = 10
    station_names = [f"{x} station name" for x in station_ids]
    nc_attributes = None
    latitudes = None
    longitudes = None
    areas = None

    def _create_test_ds():
        d = wrap.xr_efts(
            issue_times,
            station_ids,
            lead_times,
            lead_time_tstep,
            ensemble_size,
            station_names,
            nc_attributes,
            latitudes,
            longitudes,
            areas,
        )
        return EftsDataSet(d)

    # NOTE: should it be? is it wise to allow missing values for mandatory variables
    w = _create_test_ds()

    w.create_data_variables(
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
    assert w.writeable_to_stf2()
    # create a temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        filename = tmp.name
        w.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.DERIVED,
            ens=False,
            timestep="hours",
            data_qual=None,
        )
        # round trip test
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars


def test_create_new_efts_future_station_ids():
    """Placeholder test, for upcoming version of the conventions.

    Note the use of strings for station IDs, not integers.
    """
    import efts_io.wrapper as wrap

    issue_times = pd.date_range("2010-01-01", periods=31, freq="D")
    string_station_ids = ["a", "b"]
    lead_times = np.arange(start=1, stop=4, step=1)
    lead_time_tstep = "hours"
    ensemble_size = 10
    station_names = [f"{x} station name" for x in string_station_ids]
    nc_attributes = None
    latitudes = None
    longitudes = None
    areas = None

    def _create_test_ds():
        d = wrap.xr_efts(
            issue_times,
            string_station_ids,
            lead_times,
            lead_time_tstep,
            ensemble_size,
            station_names,
            nc_attributes,
            latitudes,
            longitudes,
            areas,
        )
        return EftsDataSet(d)

    # NOTE: should it be? is it wise to allow missing values for mandatory variables
    w = _create_test_ds()

    w.create_data_variables(
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
    # 2025-11 It has been decided to support transparent conversion of string station
    # IDs to integers on save for STF2.0.
    # It was otherwise confusing for users.
    # besides it helps to promote the use of string station IDs in memory datasets.
    assert w.writeable_to_stf2()
    # if w.writeable_to_stf2():
    #     raise RuntimeError("This should not be flagged as writeable to STF2.0, station IDs are strings.")


def test_repro_issue_16():
    """Try to repro as closely as possible the issue reported in #16."""
    station_ids = [1, 2, 3]
    _saving_to_stf2(station_ids)


def test_large_station_integers():
    """Try to repro as closely as possible the issue reported in #17."""
    station_ids = [1, 2, 123456789123]
    with pytest.raises(OverflowError):
        _saving_to_stf2(station_ids, intdata_type="i4", delete=False)
    _saving_to_stf2(station_ids, intdata_type="i8", delete=True)


def _saving_to_stf2(station_ids, intdata_type="i4", delete=True):
    xr_ds = xr_efts(
        issue_times=pd.date_range("2023-10-01", periods=31, freq="D"),
        station_ids=station_ids,
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
            # "STF_convention_version" can be skipped in memoy, this is added on save to stf2
            # "STF_nc_spec" can be skipped in memoy, this is added on save to stf2
        },
        areas=[10.0, 20.0, 30.0],
        latitudes=[60.0, 61.0, 62.0],
        longitudes=[10.0, 11.0, 12.0],
    )
    eds = EftsDataSet(xr_ds)
    eds.stf2_int_datatype = intdata_type
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
    assert eds.writeable_to_stf2()
    # create a temporary file
    import tempfile

    # save to STF2.0 will clean up the file if write fails,
    # so in that case we should allow for deletion to be True or False
    with tempfile.NamedTemporaryFile(suffix=".nc", delete=delete) as tmp:
        filename = tmp.name
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=DataOriginType.DERIVED,
            ens=False,
            timestep="hours",
            data_qual=None,
        )
        # round trip test
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars


def test_new_variable():
    """Test the new_variable method of EftsDataSet."""
    import efts_io.wrapper as wrap

    # Create a base dataset using existing test helper pattern
    issue_times = pd.date_range("2010-01-01", periods=10, freq="D")
    station_ids = [123, 456]
    lead_times = np.arange(start=1, stop=4, step=1)
    lead_time_tstep = "hours"
    ensemble_size = 5

    d = wrap.xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep=lead_time_tstep,
        ensemble_size=ensemble_size,
    )
    eds = EftsDataSet(d)

    # Test 1: Create a variable with automatic NaN initialization
    var_attrs = {
        "units": "mm",
        "long_name": "Test Variable",
        "comment": "This is a test variable",
    }
    new_var = eds.new_variable(
        varname="test_var",
        dim_names=["station_id", "time"],
        var_attributes=var_attrs,
    )

    assert "test_var" in eds.data.variables
    assert new_var.name == "test_var"
    assert new_var.dims == ("station_id", "time")
    assert new_var.shape == (len(station_ids), len(issue_times))
    assert np.all(np.isnan(new_var.values))
    assert new_var.attrs["units"] == "mm"
    assert new_var.attrs["long_name"] == "Test Variable"

    # Test 2: Create a variable with explicit data
    data_shape = (len(station_ids), len(issue_times))
    test_data = np.random.randn(*data_shape)
    var_attrs_2 = {
        "units": "degC",
        "long_name": "Temperature",
    }
    new_var_2 = eds.new_variable(
        varname="temperature",
        dim_names=["station_id", "time"],
        var_attributes=var_attrs_2,
        data=test_data,
    )

    assert "temperature" in eds.data.variables
    assert new_var_2.shape == data_shape
    assert np.allclose(new_var_2.values, test_data)
    assert new_var_2.attrs["units"] == "degC"

    # Test 3: Create a 4D variable (forecast-like dimensions)
    var_attrs_3 = {
        "units": "mm/h",
        "long_name": "Rainfall Rate Forecast",
    }
    new_var_3 = eds.new_variable(
        varname="rain_fcast",
        dim_names=["lead_time", "station_id", "realization", "time"],
        var_attributes=var_attrs_3,
    )

    assert "rain_fcast" in eds.data.variables
    assert new_var_3.dims == ("lead_time", "station_id", "realization", "time")
    expected_shape = (
        len(lead_times),
        len(station_ids),
        ensemble_size,
        len(issue_times),
    )
    assert new_var_3.shape == expected_shape

    # Test 4: Error when variable already exists
    with pytest.raises(ValueError, match="already exists"):
        eds.new_variable(
            varname="test_var",
            dim_names=["station_id", "time"],
            var_attributes=var_attrs,
        )

    # Test 5: Error when units attribute is missing
    with pytest.raises(ValueError, match="must include 'units'"):
        eds.new_variable(
            varname="no_units_var",
            dim_names=["station_id", "time"],
            var_attributes={"long_name": "No units"},
        )

    # Test 6: Error when data shape doesn't match dimensions
    wrong_shape_data = np.random.randn(5, 5)  # Wrong shape
    with pytest.raises(ValueError, match="does not match expected shape"):
        eds.new_variable(
            varname="wrong_shape_var",
            dim_names=["station_id", "time"],
            var_attributes={"units": "m"},
            data=wrong_shape_data,
        )

    # Test 7: Use template attributes as starting point
    template_attrs = template_variable_attributes()
    template_attrs["units"] = "m3/s"
    template_attrs["long_name"] = "Streamflow"
    new_var_4 = eds.new_variable(
        varname="streamflow",
        dim_names=["station_id", "time"],
        var_attributes=template_attrs,
    )

    assert "streamflow" in eds.data.variables
    assert new_var_4.attrs["units"] == "m3/s"
    assert new_var_4.attrs["long_name"] == "Streamflow"


def _make_stf2_roundtrip_dataset(ensemble_size, n_stations=2, n_lead_times=3, n_times=5):
    """Helper: build an EftsDataSet with a 4D variable and return (eds, shape info)."""
    issue_times = pd.date_range("2020-01-01", periods=n_times, freq="D")
    station_ids = list(range(1, n_stations + 1))
    lead_times = np.arange(1, n_lead_times + 1)

    xr_ds = xr_efts(
        issue_times=issue_times,
        station_ids=station_ids,
        lead_times=lead_times,
        lead_time_tstep="hours",
        ensemble_size=ensemble_size,
        station_names=[f"station_{i}" for i in station_ids],
        nc_attributes={
            "title": "Ensemble round-trip test",
            "institution": "Test",
            "source": "Test",
            "catchment": "Test_Catchment",
            "comment": "",
            "history": "",
        },
        latitudes=[-33.0 + i * 0.1 for i in range(n_stations)],
        longitudes=[150.0 + i * 0.1 for i in range(n_stations)],
    )
    eds = EftsDataSet(xr_ds)
    eds.create_data_variables(
        {
            "q_sim": {
                "name": "q_sim",
                "longname": "simulated streamflow",
                "units": "m3/s",
                "dim_type": "4",
                "missval": -9999.0,
                "precision": "double",
                "attributes": {},
            },
        },
    )
    return eds, issue_times, station_ids, lead_times


def test_ensemble_member_data_values_roundtrip():
    """Per-member data values must survive a full write-to-disk / reload cycle.

    Each ensemble member N is filled with a unique sentinel value N * 100.0 so that
    any axis transposition between the ensemble, station, or lead-time dimensions
    would produce wrong values and be caught immediately.
    """
    ensemble_size = 4
    n_stations = 2
    n_lead_times = 3
    n_times = 5

    eds, _, _, _ = _make_stf2_roundtrip_dataset(ensemble_size, n_stations, n_lead_times, n_times)

    # Fill each ensemble member with its own sentinel: member index i → value (i+1)*100
    # q_sim dims are (time, realization, station_id, lead_time) — C order, matching the
    # read path so that pre- and post-roundtrip arrays are always identically laid out.
    for i in range(ensemble_size):
        eds.data["q_sim"].values[:, i, :, :] = (i + 1) * 100.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="q_sim",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.SIMULATED,
            timestep="hours",
        )

        reloaded = EftsDataSet(filename)
        q = reloaded.data["q_sim"]  # dims: (lead_time, station_id, realization, time)

        # After reload the variable has C-order dims: (time, realization, station_id, lead_time)
        assert q.sizes["time"] == n_times
        assert q.sizes["realization"] == ensemble_size
        assert q.sizes["station_id"] == n_stations
        assert q.sizes["lead_time"] == n_lead_times

        for i in range(ensemble_size):
            expected = (i + 1) * 100.0
            actual = q.values[:, i, :, :]  # axis 1 is realization in C order
            assert np.all(actual == expected), (
                f"Member {i + 1}: expected all values = {expected}, got min={actual.min()}, max={actual.max()}"
            )
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_ensemble_member_ids_roundtrip():
    """Ensemble member coordinate values must round-trip as consecutive integers starting at 1.

    The STF spec defines ens_member as a vector 1:N.  After reload the realization
    coordinate in the xarray dataset must equal [1, 2, ..., N].
    """
    ensemble_size = 6

    eds, _, _, _ = _make_stf2_roundtrip_dataset(ensemble_size)
    eds.data["q_sim"].values[:] = 1.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="q_sim",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.SIMULATED,
            timestep="hours",
        )

        reloaded = EftsDataSet(filename)
        member_ids = reloaded.data["realization"].values.tolist()
        assert member_ids == list(range(1, ensemble_size + 1)), (
            f"Expected member IDs {list(range(1, ensemble_size + 1))}, got {member_ids}"
        )
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def test_non_sequential_member_ids_normalised_on_write():
    """Non-sequential realization coordinate values are normalised to [1..N] on write.

    The STF spec defines ens_member values as 1:N regardless of the xarray realization
    coordinate values in the source dataset.  This test documents that behaviour so
    that any accidental change is caught.
    """
    import xarray as xr
    from efts_io.conventions import REALISATION_DIMNAME

    ensemble_size = 3

    eds, _, _, _ = _make_stf2_roundtrip_dataset(ensemble_size)

    # Overwrite the realization coordinate with non-sequential values
    eds.data = eds.data.assign_coords(
        {REALISATION_DIMNAME: xr.DataArray([5, 10, 15], dims=[REALISATION_DIMNAME])}
    )
    eds.data["q_sim"].values[:] = 1.0

    with _temporary_named_file() as tmp:
        filename = tmp.name

    try:
        eds.save_to_stf2(
            path=filename,
            variable_name="q_sim",
            var_type=StfVariable.STREAMFLOW,
            data_type=DataOriginType.SIMULATED,
            timestep="hours",
        )

        reloaded = EftsDataSet(filename)
        member_ids = reloaded.data["realization"].values.tolist()
        assert member_ids == [1, 2, 3], (
            f"Expected normalised member IDs [1, 2, 3], got {member_ids}"
        )
    finally:
        if os.path.exists(filename):
            os.remove(filename)


if __name__ == "__main__":
    # test_read_thing()
    test_create_new_efts()
