"""Helper functions for netcdf file."""


# Initial Intent: port https://bitbucket.csiro.au/projects/SF/repos/matlab_functions/browse/Import_export/create_empty_stfnc.m
# may be an superseded feature as of July 2025

# from typing import Optional, Union

# from .wrapper import EftsDataSet

# def create_empty_stfnc(
#     ncfile: str,
#     n_stations: int,
#     var_type: Union[str, int],
#     data_type: int,
#     catchment: str = "",  # String specifying catchment name.
#     ens_no: int = 1,  # Integer specifying number of ensemble members. If you
#     fill_value: float = -9999.0,  # Fill value for the variable being created. Defaults to
#     lead_time: int = 1,  # Integer specifying forecast lead time. Only operates
#     quality: bool = False,  # Boolean. Set to true if you want to create a data quality
#     stf_nc_vers: str = "1.0",  # Double version number of STF netCDF convention. Defaults to
#     title: str = "",  # String specifying title of .nc file
#     institution: Optional[str] = None,  # String specifying institution that made the data.
#     warnings: int = 0,  # integer specifying if you wish to turn off warning
#     data_class: type = float,  # Data class for variable in .nc file. Defaults to
#     owr: bool = True,  # Bolean. Indicates whether you wish to overwrite the
# ):
#     d = EftsDataSet()

import importlib.resources


def get_sample_data_path(file_name: str) -> str:
    """Retrieve the path to a sample data file included in the package.

    Args:
        file_name (str): The name of the sample data file.

    Returns:
        str: The path to the sample data file.
    """
    with importlib.resources.path("efts_io.data", file_name) as data_path:
        return str(data_path)


def derived_rainfall_tas() -> str:
    """Sample rainfall from Tasmania."""
    sample_data_file = "derived_rainfall_tas.nc"
    return get_sample_data_path(sample_data_file)
