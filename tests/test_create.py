# import netCDF4
import numpy as np
import pandas as pd
from efts_io.wrapper import EftsDataSet

def test_create_new_efts():
    import efts_io.wrapper as wrap

    issue_times = pd.date_range("2010-01-01", periods=31, freq="D")
    station_ids = ["a", "b"]
    lead_times = np.arange(start=1, stop=4, step=1)
    lead_time_tstep = "hours"
    ensemble_size = 10
    station_names = None
    nc_attributes = None
    latitudes = None
    longitudes = None
    areas = None
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
    w = EftsDataSet(d)
    assert w.writeable_to_stf2()


if __name__ == "__main__":
    # test_read_thing()
    test_create_new_efts()
