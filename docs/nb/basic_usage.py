# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: efts-io (3.12.5)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Basic use
#
# `efts-io` is primarily about creating, handling and saving and loading ensemble forecast time series to files on disk in [netCDF STF 2.0 compliant format](https://csiro-hydroinformatics.github.io/efts-io/netcdf_for_water_forecasting/), from Python. 
#
# While most similar implementations in e.g. R, Matlab so var have been closely related to netCDF file handling, in Python [`xarray`](https://docs.xarray.dev/en/stable) is a de facto standard for the high level manipulation of tensor-like, multidimensional data. There is a partial mismatch between the STF netCDF conventions devised ten years ago and limited by the capabilities of Fortran netCDF libraries at the time, and the best practices for `xarray` in-memory representations. `efts-io` is a package bridging the technical gap between these two representations, and reducing the risk of data handling bugs by users when trying to reconcile this technical gap.

# %% [markdown]
# ## Reading from file
#
# The package includes small, sample data files. We will start with a file storing a single rainfall time series
#

# %%
import efts_io.helpers as hlp

# %%
fn = hlp.derived_rainfall_tas()

# %%
# The path to the sample file will depend on your operating system, environment setup etc.
from pathlib import Path
homepath = str(Path.home())
print(fn.replace(homepath, '/your_home_path'))

# %%
if not Path(fn).exists():
    raise FileNotFoundError(fn)

# %% [markdown]
# ### Validating compliance of a file before loading
#
# The package includes facilities to check the structure of a file on disk and its level of compliance with the STF conventions:

# %%
from efts_io.conventions import check_stf_compliance, check_hydrologic_variables

# %%
compliance_report = check_stf_compliance(fn)
print(f"compliance_report is a dictionary with keys {list(compliance_report.keys())}")
      

# %% [markdown]
# There is no error nor warnings in this sample file:

# %%
print("WARNING:", compliance_report["WARNING"])
print("ERROR:", compliance_report["ERROR"])

# %% [markdown]
# To get a detail of what was checked in the file structure:

# %%
print("INFO:", compliance_report["INFO"])

# %% [markdown]
# If we use the venerable `ncdump` command line tool, (just to give a low-level overview of the file):

# %%
# !ncdump -h {fn}

# %% [markdown]
# ### Checking variables
#
# `check_hydrologic_variables` looks into more details at the variables present in the netcdf file. The STF convention suggests naming conventions, as well as the expectation of certain variable attributes. 

# %%
compliance_report = check_hydrologic_variables(fn)

# %%
compliance_report

# %%
print("INFO:", compliance_report["INFO"])
print("WARNING:", compliance_report["WARNING"])
print("ERROR:", compliance_report["ERROR"])

# %% [markdown]
# Two of the variable attributes in the file happen to not quite follow strictly the STF conventions, but in this case this is not a blocking incompatibility.

# %% [markdown]
# ### Loading data
#
# We recommend loading the files using a thin wrapper around an `xarray` object called `EftsDataSet`.
#
# If you were to open the file directly using `xarray`, you would encounter an error

# %%
try:
    import xarray as xr
    xr.open_dataset(fn)
except ValueError as e:
    print(e)

# %% [markdown]
# `EftsDataSet` takes care of the low-level acrobatics required to read STF files, which was designed before `xarray` emerged and gained popularity. 

# %%
from efts_io.wrapper import EftsDataSet
rain_stf = EftsDataSet(fn)

# %% [markdown]
# There are helper methods on `EftsDataSet` objects, but most add little value so far to the inner `xarray` object. Note that the in-memory `xarray` structure has a coordinate in a form of a string for `station_id`, rather than an integer as is specified in the STF 2.0 convention for on-disk netCDF storage. This is a deliberate choice, as we envisage that ulterior versions of the conventions will feature strings for station identifiers. Limiting station identifiers to integers is in part a legacy of using the Fortran programming language in the past.
#
# Details of a conversation about data design can be found in [this thread](https://github.com/csiro-hydroinformatics/efts-io/issues/2).

# %%
print(rain_stf.data)

# %% [markdown]
# ## Saving a STF 2.0 file
#
# Since the data was loaded from an STF 2.0 file, one would hope we can round trip and save to disk. The method `writeable_to_stf2` performs checks on the in-memory representation, to determine if it has the information to create a compliant netCDF file. In this case, unsurprisingly:
#

# %%
rain_stf.writeable_to_stf2()

# %%
import tempfile

# %%
out_fn = tempfile.NamedTemporaryFile().name

# %%
out_fn

# %%
Path(out_fn).exists()

# %%
from efts_io.wrapper import StfVariable
from efts_io.conventions import DataOriginType

# %%
rain_stf.save_to_stf2(
    path=out_fn,
    variable_name="rain_obs",
    var_type=StfVariable.RAINFALL,
    data_type=DataOriginType.DERIVED,
    ens=True,
    timestep="days",
    data_qual=None,
)

# %%
compliance_report = check_stf_compliance(out_fn)

# %% [markdown]
# One would hope that what the package writes out passes the low-level checks:

# %%
print("WARNING:", compliance_report["WARNING"])
print("ERROR:", compliance_report["ERROR"])

# %%
print("INFO:", compliance_report["INFO"])

# %% [markdown]
# Let's clean up the temporary file, in case the operating system does not later on.

# %%
import os, time

time.sleep(1) # limit the risk of file lock on the output file.
if Path(out_fn).exists():
    os.remove(out_fn)

# %% [markdown]
# ## Creating a new STF xarray dataset
#
# **UNDER CONSTRUCTION**. This will probably be revised.
#
# There are several ways to create a dataset for ensemble forecast time series with `efts-io`. One helper function to create a data set is [`xr_efts`](https://csiro-hydroinformatics.github.io/efts-io/reference/efts_io/wrapper/?h=xr_efts#efts_io.wrapper.xr_efts), particularly if you know upfront the geometry (dimensions) of your dataset:

# %%
import pandas as pd
import numpy as np

# %%
from efts_io import wrapper as w

# %%
issue_times = pd.date_range("2010-01-01", periods=31, freq="D")
station_ids = ["410088","410776"]
lead_times = np.arange(start=1, stop=4, step=1)
lead_time_tstep = "hours"
ensemble_size = 10
station_names= ["GOODRADIGBEE B/BELLA", "Licking Hole Ck"]# None
latitudes = None
longitudes = None
areas = None


# %%

nc_attributes = w.create_mandatory_global_attributes(
    title="Example dataset",
    institution="My organisation",
    catchment="Some catchment",
    source="Synthetic data generated for testing purposes",
    comment="This dataset is from a tutorial and should not be used for any purpose other than testing the efts-io library.",
    history=None, # will create a default time stamp
)
nc_attributes



# %%

d = w.xr_efts(
    issue_times,
    station_ids,
    lead_times,
    lead_time_tstep,
    ensemble_size,
    station_names,
    latitudes,
    longitudes,
    areas,
    nc_attributes,
)


# %% [markdown]
# Let us have a look at the created Dataset:

# %%
d

# %% [markdown]
# ### Adding a data variable
#
# The dataset above has coordinates but not yet data.

# %%
eds = EftsDataSet(d)


# %%
# eds.new_variable?

# %% [markdown]
# ### Metadata
#
# `var_attributes`

# %%
from efts_io.attributes import (
    create_variable_attributes,
    TimeSeriesType,
    DataOriginType,
    LocationType
)


# %%
var_attrs = create_variable_attributes(
    long_name="synthetic streamflow",
    units="m3/s",
    time_series_type=TimeSeriesType.AVERAGED,
    data_origin=DataOriginType.SIMULATED,
    data_description="Goodradigbee dummy flows",
    location_type=LocationType.POINT,
)
var_attrs

# %% [markdown]
#

# %%

new_var_4 = eds.new_variable(
    varname="streamflow",
    dim_names=["station_id", "time"],
    var_attributes=var_attrs,
    data=np.random.rand(len(station_ids), len(issue_times)),
)


# %%
eds.writeable_to_stf2()

