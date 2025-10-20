# import netCDF4
import numpy as np
import pandas as pd
import pytest
from efts_io._ncdf_stf2 import StfDataType, StfVariable
from efts_io.wrapper import EftsDataSet, xr_efts


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
        }
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
            data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
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
        }
    )
    if w.writeable_to_stf2():
        raise RuntimeError("This should not be flagged as writeable to STF2.0, station IDs are strings.")


def test_repro_issue_16():
    """Try to repro as closely as possible the issue reported in #16."""
    station_ids = [1, 2, 3]
    _saving_to_stf2(station_ids)


def test_large_station_integers():
    """Try to repro as closely as possible the issue reported in #17."""
    station_ids = [1, 2, 123456789123]
    with pytest.raises(OverflowError):
        _saving_to_stf2(station_ids, intdata_type="i4")
    _saving_to_stf2(station_ids, intdata_type="i8")


def _saving_to_stf2(station_ids, intdata_type="i4"):
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
        }
    )
    assert eds.writeable_to_stf2()
    # create a temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        filename = tmp.name
        eds.save_to_stf2(
            path=filename,
            variable_name="rain_obs",
            var_type=StfVariable.RAINFALL,
            data_type=StfDataType.DERIVED_FROM_OBSERVATIONS,
            ens=False,
            timestep="hours",
            data_qual=None,
        )
        # round trip test
        ds = EftsDataSet(filename)
        assert "rain_obs" in ds.data.data_vars


if __name__ == "__main__":
    # test_read_thing()
    test_create_new_efts()
