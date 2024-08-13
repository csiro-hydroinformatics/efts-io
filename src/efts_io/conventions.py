"""Naming conventions for the EFTS netCDF file format."""

from typing import List, Optional

TIME_DIMNAME = "time"

stations_dim_name = "station"
lead_time_dim_name = "lead_time"
time_dim_name = "time"
ensemble_member_dim_name = "ens_member"
str_length_dim_name = "str_len"

# int station_id[station]
station_id_varname = "station_id"
# char station_name[str_len,station]
station_name_varname = "station_name"
# float lat[station]
lat_varname = "lat"
# float lon[station]
lon_varname = "lon"
# float x[station]
x_varname = "x"
# float y[station]
y_varname = "y"
# float area[station]
area_varname = "area"
# float elevation[station]
elevation_varname = "elevation"

conventional_varnames = [
    stations_dim_name,
    lead_time_dim_name,
    time_dim_name,
    ensemble_member_dim_name,
    str_length_dim_name,
    station_id_varname,
    station_name_varname,
    lat_varname,
    lon_varname,
    x_varname,
    y_varname,
    area_varname,
    elevation_varname,
]

mandatory_global_attributes = ["title", "institution", "source", "catchment", "comment"]


def get_default_dim_order() -> List[str]:
    """Default order of dimensions in the netCDF file.

    Returns:
        List[str]: dimension names: [lead_time, stations, ensemble_member, time]
    """
    return [
        lead_time_dim_name,
        stations_dim_name,
        ensemble_member_dim_name,
        time_dim_name,
    ]


def check_index_found(index_id: Optional[int], identifier: str, dimension_id: str) -> None:
    """Helper function to check that a value (index) was is indeed found in the dimension."""
    # return isinstance(index_id, np.int64)
    if index_id is None:
        raise ValueError(f"identifier '{identifier}' not found in the dimension '{dimension_id}'")
