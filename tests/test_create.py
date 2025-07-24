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
    # assert w.writeable_to_stf2()
    # w.save_to_stf2()


if __name__ == "__main__":
    # test_read_thing()
    test_create_new_efts()
