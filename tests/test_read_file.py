import os
from typing import Optional

# import netCDF4
import numpy as np
import pandas as pd

from efts_io.dimensions import create_time_info, create_timestamps
from efts_io.wrapper import EftsDataSet

pkg_dir = os.path.join(os.path.dirname(__file__), "..")

variable_names = ["variable_1", "variable_2"]
station_ids_ints = [123, 456]

nEns = 3
nLead = 4
x = np.arange(1, (nEns * nLead) + 1)
x = x.reshape((nLead, nEns))
y = x + nEns * nLead

timeAxisStart = pd.Timestamp(
    year=2010,
    month=8,
    day=1,
    hour=12,
    minute=0,
    second=0,
    tz="UTC",
)
tested_fcast_issue_time = timeAxisStart + pd.Timedelta(6, "h")
v1 = variable_names[0]
s1 = station_ids_ints[0]
v2 = variable_names[1]
s2 = station_ids_ints[1]


def dhours(i):
    return pd.Timedelta(i, "h")


def ddays(i):
    return pd.Timedelta(i * 24, "h")


import pytest


@pytest.mark.skip(reason="Ported from the R package, but may not be relevant or the best approach anymore")
def test_read_thing():
    fn = os.path.join(pkg_dir, "tests", "data", "hourly_test.nc")
    assert os.path.exists(fn)
    ds = EftsDataSet(fn)
    assert set(ds.get_dim_names()) == {"ens_member", "lead_time", "station", "str_len", "time"}
    r1 = ds.get_ensemble_forecasts(
        variable_name=v1,
        identifier=s1,
        start_time=tested_fcast_issue_time,
    )
    r2 = ds.get_ensemble_forecasts(
        variable_name=v2,
        identifier=s2,
        start_time=tested_fcast_issue_time,
    )
    assert r1[1, 1] == 6
    assert r2[1, 1] == 18
    # Check the lead time axix:
    # fcast_timeaxis = index(r1)
    # assert (fcast_timeaxis[0], tested_fcast_issue_time + lead_ts(lead_time_step_start_offset))
    # assert (fcast_timeaxis[1], tested_fcast_issue_time + lead_ts(lead_time_step_start_offset + lead_time_step_delta))


def _do_time_axis_test(
    tstart: pd.Timestamp,
    time_step: str = "days since",
    time_step_delta: int = 1,
    n: int = 10,
    tz_str: Optional[str] = None,
    expected_offset: Optional[pd.DateOffset] = None,
):
    time_dim_info = create_time_info(
        start=tstart,
        n=n,
        time_step=time_step,
        time_step_delta=time_step_delta,
    )
    timestamps = create_timestamps(time_dim_info, tz_str)
    expected_timestamps = [tstart + expected_offset * i for i in range(n)]
    assert np.all(timestamps == expected_timestamps)


def test_time_axis():
    n = 10
    tz_str = "UTC"
    tstart = pd.Timestamp(
        year=2010,
        month=8,
        day=1,
        hour=23,
        minute=0,
        second=0,
        tz=tz_str,
    )

    for time_step, time_step_delta, expected_offset in [
        ("hours since", 1, pd.DateOffset(hours=1)),
        ("hours since", 3, pd.DateOffset(hours=3)),
        ("days since", 1, pd.DateOffset(days=1)),
        ("days since", 3, pd.DateOffset(days=3)),
        # TODO
        # ("weeks since", 1, pd.DateOffset(weeks=1)),
        # ("months since", 1, pd.DateOffset(months=1)),
    ]:
        _do_time_axis_test(
            tstart,
            time_step,
            time_step_delta,
            n,
            tz_str=tz_str,
            expected_offset=expected_offset,
        )


# put tests in a tryCatch, to maximise the chances of cleaning up temporary
# files.
def doTests(
    tempNcFname,
    lead_time_tstep="hours",
    time_step="hours since",
    time_step_delta=1,
    lead_time_step_start_offset=1,
    lead_time_step_delta=1,
):
    # lead_time_tstep = "days"
    # time_step = "days since"
    # time_step_delta = 1L
    # lead_time_step_start_offset = 1L
    # lead_time_step_delta = 1L

    case_params = "".join(
        [
            "lts=",
            lead_time_tstep,
            ",ts=",
            time_step,
            ",tsdelta=",
            str(time_step_delta),
            ",ltsoffset=",
            str(lead_time_step_start_offset),
            ",ltsdelta=",
            str(lead_time_step_delta),
        ],
    )
    from efts_io.dimensions import create_time_info

    time_dim_info = create_time_info(
        start=timeAxisStart,
        n=10,
        time_step=time_step,
        time_step_delta=time_step_delta,
    )

    n = len(variable_names)
    varsDef = pd.DataFrame.from_dict(
        {
            "name": variable_names,
            "longname": ["long name for " + name for name in variable_names],
            UNITS_ATTR_KEY: np.repeat("mm", n),
            "missval": np.repeat(-999, n),
            "precision": np.repeat("double", n),
            TYPE_ATTR_KEY: np.repeat(2, n),
            "dimensions": np.repeat("4", n),
            TYPE_DESCRIPTION_ATTR_KEY: np.repeat("accumulated over the previous time step", n),
            LOCATION_TYPE_ATTR_KEY: np.repeat("Point", n),
        },
    )
    from efts_io.attributes import create_global_attributes

    glob_attr = create_global_attributes(
        title="title test",
        institution="test",
        source="test",
        catchment="dummy",
        comment="none",
    )

    from efts_io.variables import create_variable_definitions

    var_defs_dict = create_variable_definitions(varsDef)
    lead_times_offsets = (
        np.arange(lead_time_step_start_offset, lead_time_step_start_offset + nLead) * lead_time_step_delta
    )

    tz_str = "UTC"

    issue_times = create_timestamps(time_dim_info, tz_str)
    from efts_io.wrapper import xr_efts

    # TODO: expand to test non-integer station_ids
    station_ids = [str(i) for i in station_ids_ints]
    ensemble_size = nEns
    station_names = ["station_" + str(i) for i in station_ids_ints]
    xr_data = xr_efts(
        issue_times,
        station_ids,
        lead_times_offsets,
        lead_time_tstep,
        ensemble_size,
        station_names,
        nc_attributes=glob_attr,
    )

    # snc = create_efts(
    #     tempNcFname,
    #     time_dim_info,
    #     var_defs_dict,
    #     station_ids_ints,
    #     nc_attributes=glob_attr,
    #     lead_length=nLead,
    #     ensemble_length=nEns,
    #     lead_time_tstep=lead_time_tstep,
    # )
    snc = EftsDataSet(xr_data)

    snc.create_data_variables(var_defs_dict)

    snc.put_ensemble_forecasts(
        x,
        variable_name=v1,
        identifier=s1,
        start_time=tested_fcast_issue_time,
    )
    snc.put_ensemble_forecasts(
        y,
        variable_name=v2,
        identifier=s2,
        start_time=tested_fcast_issue_time,
    )

    r1 = snc.get_ensemble_forecasts(
        variable_name=v1,
        identifier=s1,
        start_time=tested_fcast_issue_time,
    )
    r2 = snc.get_ensemble_forecasts(
        variable_name=v2,
        identifier=s2,
        start_time=tested_fcast_issue_time,
    )
    assert r1[1, 1] == 6
    assert r2[1, 1] == 18
    snc.write()

    if lead_time_tstep == "hours":
        lead_ts = dhours
    elif lead_time_tstep == "days":
        lead_ts = ddays

    snc.to_netcdf(tempNcFname)

    from efts_io.wrapper import open_efts

    snc = open_efts(tempNcFname)
    r1 = snc.get_ensemble_forecasts(
        variable_name=v1,
        identifier=s1,
        start_time=tested_fcast_issue_time,
    )
    r2 = snc.get_ensemble_forecasts(
        variable_name=v2,
        identifier=s2,
        start_time=tested_fcast_issue_time,
    )
    assert r1[1, 1] == 6
    assert r2[1, 1] == 18
    # Check the lead time axix:
    fcast_timeaxis = r1.lead_time
    assert fcast_timeaxis[0] == tested_fcast_issue_time + lead_ts(
        lead_time_step_start_offset,
    )
    assert fcast_timeaxis[1] == tested_fcast_issue_time + lead_ts(
        lead_time_step_start_offset + lead_time_step_delta,
    )
    snc.close()


import tempfile
import pytest


@pytest.mark.skip(reason="Ported from the R package, but may not be relevant or the best approach anymore")
def test_round_trip():
    with tempfile.TemporaryDirectory() as temp_dir:
        tested_fcast_issue_time = timeAxisStart + ddays(2)
        # Covers https://github.com/jmp75/efts/issues/6
        tempNcFname = os.path.join(temp_dir, "days.nc")
        doTests(
            tempNcFname,
            lead_time_tstep="days",
            time_step="days since",
            time_step_delta=1,
            lead_time_step_start_offset=1,
            lead_time_step_delta=1,
        )

        tested_fcast_issue_time = timeAxisStart + dhours(6)

        tempNcFname = os.path.join(temp_dir, "hourly.nc")
        doTests(
            tempNcFname,
            lead_time_tstep="hours",
            time_step="hours since",
            time_step_delta=1,
            lead_time_step_start_offset=1,
            lead_time_step_delta=1,
        )

        tempNcFname = os.path.join(temp_dir, "three_hourly.nc")
        doTests(
            tempNcFname,
            lead_time_tstep="hours",
            time_step="hours since",
            time_step_delta=1,
            lead_time_step_start_offset=1,
            lead_time_step_delta=3,
        )


if __name__ == "__main__":
    # test_time_axis()
    # test_read_thing()
    test_round_trip()
