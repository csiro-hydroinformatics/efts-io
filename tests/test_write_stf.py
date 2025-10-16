from typing import Iterable
import pytest
import numpy as np
import xarray as xr
from efts_io._ncdf_stf2 import make_ready_for_saving
import pandas as pd

from efts_io.conventions import (
    ENS_MEMBER_DIMNAME,
    STATION_DIMNAME,
    TIME_DIMNAME,
    STATION_ID_DIMNAME,
    LEAD_TIME_DIMNAME,
    REALISATION_DIMNAME,
    STATION_NAME_VARNAME,
    LAT_VARNAME,
    LON_VARNAME,
    xr_to_stf_dims,
    stf_to_xr_dims,
)


def sample_dataset(
    n_time=5,
    n_stations=2,
    n_lead_time=3,
    n_realisations=4,
):
    """Create a sample dataset with all required coordinates."""
    stations_nbs = np.arange(n_stations)
    ds = xr.Dataset(
        coords={
            TIME_DIMNAME: pd.date_range("2023-01-01", periods=n_time),
            STATION_ID_DIMNAME: [f"station_{i}" for i in range(n_stations)],
            LEAD_TIME_DIMNAME: list(range(n_lead_time)),
            REALISATION_DIMNAME: list(range(n_realisations)),
        },
        data_vars={
            # STATION_ID_VARNAME: xr.DataArray([1, 2, 3], dims=[STATION_ID_DIMNAME]),
            STATION_NAME_VARNAME: xr.DataArray(
                [f"station_{i} name" for i in range(n_stations)], dims=[STATION_ID_DIMNAME]
            ),
            LAT_VARNAME: xr.DataArray(1.1 * stations_nbs, dims=[STATION_ID_DIMNAME]),
            LON_VARNAME: xr.DataArray(100.0 + stations_nbs, dims=[STATION_ID_DIMNAME]),
        },
    )
    return ds


def stf_dimensions_order():
    """Return the standard STF dimensions order for NetCDF files."""
    return (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)


def xr_dimensions_order():
    """Return the corresponding xarray dimensions order."""
    return (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)


import numpy as np
import xarray as xr


def create_data_array(
    stf_equivalent_dimensions: Iterable[str],
    dataset: xr.Dataset,
) -> xr.DataArray:
    """Helper function to create a test DataArray with specific dimensions.

    Args:
        stf_equivalent_dimensions (list): List of dimension names in STF equivalent order.
          The sample data will be created with equivalent dimensions in the xarray form
        dataset (xr.Dataset, optional): Dataset to use for coordinates if available.

    Returns:
        xr.DataArray: DataArray with specified dimensions and data.
    """
    xr_dimensions = [stf_to_xr_dims[x] if x in stf_to_xr_dims else x for x in stf_equivalent_dimensions]
    if dataset is not None:
        dimsizes = {x: len(dataset.coords[x]) if x in xr_to_stf_dims else 2 for x in xr_dimensions}
    else:
        dimsizes = {}
    shape = tuple(dimsizes[dim] if dim in dimsizes else 2 for dim in xr_dimensions)

    # Create data with the specified shape based on dimension indices
    data = np.zeros(shape)
    for idx, dim in enumerate(xr_dimensions):
        if dim == TIME_DIMNAME:
            data += 1 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == STATION_ID_DIMNAME:
            data += 0.1 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == LEAD_TIME_DIMNAME:
            data += 0.01 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])
        elif dim == REALISATION_DIMNAME:
            data += 0.001 * np.arange(shape[idx]).reshape([shape[i] if i == idx else 1 for i in range(len(shape))])

    # If dataset is provided, use its coordinates
    if dataset is not None:
        coords = {dim: dataset[dim] if dim in dataset.coords else np.arange(2) for dim in xr_dimensions}
        return xr.DataArray(data, dims=xr_dimensions, coords=coords)
    else:
        return xr.DataArray(data, dims=xr_dimensions)


# mini tests for the test dataset creators:


def test_create_data_array_with_all_dimensions():
    """Test the creation of a DataArray with all specified dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    stf_equivalent_dimensions = stf_dimensions_order()
    data_array = create_data_array(stf_equivalent_dimensions, dataset)

    assert data_array.dims == xr_dimensions_order()
    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert data_array.shape == (5, 4, 2, 3)


def test_create_data_array_with_missing_dimensions():
    """Test the creation of a DataArray with missing dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    stf_equivalent_dimensions = (TIME_DIMNAME, STATION_DIMNAME)
    data_array = create_data_array(stf_equivalent_dimensions, dataset)

    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert data_array.dims == (TIME_DIMNAME, STATION_ID_DIMNAME)
    assert data_array.shape == (5, 2)


def test_create_data_array_without_dataset():
    """Test the creation of a DataArray without a dataset."""
    stf_equivalent_dimensions = (TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME)
    data_array = create_data_array(stf_equivalent_dimensions, None)

    assert data_array.dims == (TIME_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME, REALISATION_DIMNAME)
    assert data_array.shape == (2, 2, 2, 2)  # Default shape when dataset is None


# Testing `make_ready_for_saving`


def _check_all_four_dims(dimensions_order):
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    data = create_data_array(dimensions_order, dataset)
    result = make_ready_for_saving(data, dataset, stf_dimensions_order())

    assert result.dims == xr_dimensions_order()
    assert result.shape == (5, 4, 2, 3)


def test_presave_with_all_dimensions_standard_order():
    """Test the transformation of a DataArray with all required dimensions."""
    dimensions_order = stf_dimensions_order()
    _check_all_four_dims(dimensions_order)


def test_presave_with_all_dimensions_different_order():
    """Test the transformation of a DataArray with all required dimensions."""
    dimensions_order = stf_dimensions_order()[::-1]
    _check_all_four_dims(dimensions_order)


def test_presave_with_missing_dimensions():
    """Test the transformation of a DataArray with missing dimensions."""
    a_dimensions = (TIME_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)
    # no ENS_MEMBER_DIMNAME,
    # First, let us assume a the dataset has a ENS_MEMBER_DIMNAME dim of 1
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=1)
    data = create_data_array(a_dimensions, dataset)
    result = make_ready_for_saving(data, dataset, stf_dimensions_order())
    assert result.dims == xr_dimensions_order()
    # (TIME_DIMNAME, REALISATION_DIMNAME, STATION_ID_DIMNAME, LEAD_TIME_DIMNAME)
    assert result.shape == (5, 1, 2, 3)
    # however if the dataset has more than one realisation, this is problematic
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=3)
    data = create_data_array(a_dimensions, dataset)
    with pytest.raises(ValueError):
        result = make_ready_for_saving(data, dataset, stf_dimensions_order())


def test_presave_with_invalid_dimensions():
    """Test the transformation of a DataArray with invalid dimensions."""
    dataset = sample_dataset(n_time=5, n_stations=2, n_lead_time=3, n_realisations=4)
    data = xr.DataArray(np.random.rand(5, 2), dims=(TIME_DIMNAME, "invalid_dim"))
    dimensions_order = (TIME_DIMNAME, ENS_MEMBER_DIMNAME, STATION_DIMNAME, LEAD_TIME_DIMNAME)

    with pytest.raises(ValueError):
        _ = make_ready_for_saving(data, dataset, stf_dimensions_order())

    # TODO: following a tad superfluous perhaps, and cannot get the test data creation to work yet
    # data_dimensions = ("invalid_dim",) + dimensions_order
    # data = create_data_array(data_dimensions, dataset)
    # with pytest.raises(ValueError):
    #     _ = make_ready_for_saving(data, dataset, stf_dimensions_order())
