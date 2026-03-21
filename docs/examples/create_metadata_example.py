"""Example: Creating metadata attributes for STF 2.0 netCDF variables.

This script demonstrates the improved API for creating variable attributes
that comply with the STF 2.0 conventions using type-safe enumerations.
"""

import numpy as np
import pandas as pd

from efts_io import EftsDataSet, xr_efts
from efts_io.attributes import (
    DataOriginType,
    LocationType,
    TimeSeriesType,
    create_variable_attributes,
)


def main():
    """Demonstrate creating attributes using the new type-safe API."""
    print("=" * 70)
    print("Creating Metadata Attributes - New API Demo")
    print("=" * 70)

    # ==========================================================================
    # Example 1: Create attributes using enumerations (RECOMMENDED)
    # ==========================================================================
    print("\n1. Creating attributes with type-safe enumerations")
    print("-" * 70)

    rain_attrs = create_variable_attributes(
        long_name="observed rainfall",
        units="mm",
        time_series_type=TimeSeriesType.ACCUMULATED,
        data_origin=DataOriginType.OBSERVED,
        data_description="gauge measurements from station network",
        location_type=LocationType.POINT,
        fill_value=-9999.0,
    )

    print("Attributes for observed rainfall:")
    for key, value in rain_attrs.items():
        print(f"  {key}: {value}")

    # ==========================================================================
    # Example 2: Different variable types
    # ==========================================================================
    print("\n2. Creating attributes for different variable types")
    print("-" * 70)

    # Simulated streamflow (averaged over interval)
    flow_sim_attrs = create_variable_attributes(
        long_name="simulated streamflow",
        units="m3/s",
        time_series_type=TimeSeriesType.AVERAGED,
        data_origin=DataOriginType.SIMULATED,
        data_description="GR4H model output forced with observed rainfall",
    )

    print("Simulated streamflow attributes:")
    print(f"  type: {flow_sim_attrs['type']} ({flow_sim_attrs['type_description']})")
    print(f"  dat_type: {flow_sim_attrs['dat_type']}")

    # Forecast streamflow
    flow_fct_attrs = create_variable_attributes(
        long_name="forecast streamflow",
        units="m3/s",
        time_series_type=TimeSeriesType.AVERAGED,
        data_origin=DataOriginType.FORECAST,
        data_description="GR4H model forecast forced with NWP rainfall",
    )

    print("\nForecast streamflow attributes:")
    print(f"  type: {flow_fct_attrs['type']} ({flow_fct_attrs['type_description']})")
    print(f"  dat_type: {flow_fct_attrs['dat_type']}")

    # Instantaneous stage height
    stage_attrs = create_variable_attributes(
        long_name="observed stage height",
        units="m",
        time_series_type=TimeSeriesType.INSTANTANEOUS,
        data_origin=DataOriginType.OBSERVED,
        data_description="water level measurements",
    )

    print("\nStage height attributes:")
    print(f"  type: {stage_attrs['type']} ({stage_attrs['type_description']})")

    # Temperature (point in interval)
    temp_attrs = create_variable_attributes(
        long_name="maximum temperature",
        units="°C",
        time_series_type=TimeSeriesType.POINT_IN_INTERVAL,
        data_origin=DataOriginType.OBSERVED,
        data_description="daily maximum temperature recorded",
    )

    print("\nMaximum temperature attributes:")
    print(f"  type: {temp_attrs['type']} ({temp_attrs['type_description']})")

    # ==========================================================================
    # Example 3: Using attributes with EftsDataSet
    # ==========================================================================
    print("\n3. Using attributes in an EftsDataSet")
    print("-" * 70)

    # Create a simple dataset
    times = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
    station_ids = ["station_1", "station_2"]

    dataset = xr_efts(
        issue_times=times,
        station_ids=station_ids,
        nc_attributes={
            "title": "Example dataset with type-safe metadata",
            "institution": "Example Organization",
            "source": "Example model",
            "catchment": "Test_Catchment",
            "comment": "Demonstrating new metadata API",
            "history": "Created for documentation",
        },
    )

    eds = EftsDataSet(dataset)

    # Add a rainfall variable
    rain_data = np.random.rand(len(station_ids), len(times)) * 10
    eds.new_variable(
        varname="rain_obs",
        dim_names=["station_id", "time"],
        var_attributes=rain_attrs,
        data=rain_data,
    )

    print(f"Created variable 'rain_obs' with shape {eds.data['rain_obs'].shape}")
    print("Variable attributes:")
    for key, value in eds.data["rain_obs"].attrs.items():
        print(f"  {key}: {value}")

    # Add a streamflow variable
    flow_data = np.random.rand(len(station_ids), len(times)) * 50
    eds.new_variable(
        varname="q_sim",
        dim_names=["station_id", "time"],
        var_attributes=flow_sim_attrs,
        data=flow_data,
    )

    print(f"\nCreated variable 'q_sim' with shape {eds.data['q_sim'].shape}")

    # ==========================================================================
    # Example 4: Show all available enumeration values
    # ==========================================================================
    print("\n4. Available enumeration values")
    print("-" * 70)

    print("\nTimeSeriesType options:")
    for ts_type in TimeSeriesType:
        print(f"  {ts_type.name:35s} - Code: {ts_type.code:2d}, {ts_type.description}")

    print("\nDataOriginType options:")
    for do_type in DataOriginType:
        print(f"  {do_type.name:10s} - Code: '{do_type.code}', {do_type.description}")

    print("\nLocationType options:")
    for loc_type in LocationType:
        print(f"  {loc_type.name:5s} - Value: '{loc_type.value}'")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
