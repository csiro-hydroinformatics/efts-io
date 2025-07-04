"""Low level function to write an xarray dataarray to disk in the sft conventions.
"""

import os
from datetime import datetime
from typing import Dict

import numpy as np
import xarray as xr
from netCDF4 import Dataset
from netcdf_utility import nc_utils


def write_nc_stf2(out_nc_file: str, data: xr.DataArray, var_type =  1, data_type = 3,
                STF_nc_vers = 2, ens = False, timestep = 'days', dataQual:xr.DataArray = None, overwrite=True,
                loc_info: Dict[str,any]= None, global_att: Dict[str,any] = None):
    
    intData_type = 'i4'
    #var_type    -   Integer specifying the variable, as follows:
    #                   1 - streamflow
    #                   2 - potential evapotranspiration
    #                   3 - rainfall
    #                   4 - snow water equivalent
    #                   5 - minimum temperature
    #                   6 - maximum temperature
    
    #data_type   -   Integer specifying the data type of the variable, as
    #                   follows:
    #                   1 - derived from observations
    #                   2 - forecast
    #                   3 - observed
    #                   4 - simulated
    
    n_stations = len(data['station'])
    if global_att is None:
        nc_title=''
        catchment=''
        inst='CSIRO Environment'
        comment=''
        source=''
    else:
        nc_title=global_att['nc_title']
        catchment=global_att['catchment']
        inst = global_att['inst']
        comment = global_att['comment']
        source = global_att['source']
    
    station = np.arange(1, n_stations+1)
    if loc_info is None:
        station_id = np.arange(1, n_stations+1)
        station_name = [str(num) for num in station_id]
        subXCentroid = np.nan
        subYCentroid = np.nan
        subArea = np.nan
        other_station_id = ''
        
    else:
        station_id = loc_info['station_id']
        station_name = loc_info['station_name']
        subXCentroid = loc_info['subXCentroid']
        subYCentroid = loc_info['subYCentroid']
        subArea = loc_info['subArea']
        other_station_id = loc_info['other_station_id']
           
    
    if timestep in ['weeks', 'w', 'wk', 'week']:
        timestep_str = 'weeks'
    elif timestep in ['days', 'd', 'ds', 'day']:
        timestep_str = 'days'
    elif timestep in ['hours', 'h', 'hr', 'hour']:
        timestep_str = 'hours'
    elif timestep in ['minutes', 'm', 'min', 'minute']:
        timestep_str = 'minutes'
    elif timestep in ['seconds', 's', 'sec', 'second']:
        timestep_str = 'seconds'
    else:
        raise Exception(f"xr_open_dataset_fast has not been implemented for {timestep} unit") 
        
    # Check if file exists
    if os.path.exists(out_nc_file):
        if not overwrite:
            print(f"Warning: The file '{out_nc_file}' exists, so either set overwrite=True to overwrite or give new filename.")
            pass
        else:
            os.remove(out_nc_file)
            print(f"Warning: The file '{out_nc_file}' has been overwritten.")
    
    # Create netcdf file    
    ncfile = Dataset(out_nc_file, 'w', format='NETCDF4')
    # Global Attributes
    #ncfile.description = 'CCLIR forecasts'
    ncfile.history = 'Created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    ncfile.title = nc_title
    ncfile.institution = inst
    ncfile.source = source
    ncfile.catchment = catchment
    ncfile.STF_convention_version = STF_nc_vers
    ncfile.STF_nc_spec = 'https://wiki.csiro.au/display/wirada/NetCDF+for+SWIFT'
    ncfile.comment = comment
         
    #  station
    # --------------------
    ncfile.createDimension('station', n_stations)
    station_var = ncfile.createVariable('station', intData_type, ('station',), fill_value=-9999)
    station_var[:] = station

    #  station_id
    station_id_var = ncfile.createVariable('station_id', intData_type, ('station',), fill_value=-9999)
    station_id_var.setncattr('long_name', 'station or node identification code')
    station_id_var[:] = station_id

    #  station_name
    ncfile.createDimension('strLen', 30)
    station_name_var = ncfile.createVariable('station_name', 'c', ('station', 'strLen'))
    station_name_var.setncattr('long_name', 'station or node name')
    for s_i, stn_name in enumerate(station_name):
        char_stn_name = [' '] * 30  # 30 char length
        stn_name = stn_name[:30]
        char_stn_name[:len(stn_name)] = stn_name
        station_name_var[s_i, :] = char_stn_name

    # additional station id e.g. BoM   
    other_station_id_var = ncfile.createVariable('other_station_id', 'c', ('station', 'strLen'))
    other_station_id_var.setncattr('long_name', 'other station id e.g. BoM')
    for s_i, stn_name in enumerate(other_station_id):
        char_stn_name = [' '] * 30  # 30 char length
        stn_name = stn_name[:30]
        char_stn_name[:len(stn_name)] = stn_name
        other_station_id_var[s_i, :] = char_stn_name
    # coordinates, area
    # --------------------
    lat_var = ncfile.createVariable('lat', 'f', ('station', ), fill_value=-9999)
    lat_var.setncattr('long_name', 'latitude')
    lat_var.setncattr('units', 'degrees_north')
    lat_var.setncattr('axis', 'y')
    lat_var[:] = subYCentroid
    
    lon_var = ncfile.createVariable('lon', 'f', ('station',), fill_value=-9999)
    lon_var.setncattr('long_name', 'longitude')
    lon_var.setncattr('units', 'degrees_east')
    lon_var.setncattr('axis', 'x')
    lon_var[:] = subXCentroid

    area_var = ncfile.createVariable('area', 'f', ('station',), fill_value=-9999)
    area_var[:] = subArea

    # lead time
    # ------------
    ncfile.createDimension('lead_time', len(data['lead_time']))
    lt_var = ncfile.createVariable('lead_time', intData_type, ('lead_time',), fill_value=-9999)
    lt_var.setncattr('standard_name', 'lead time')
    lt_var.setncattr('long_name', 'forecast lead time')
    lt_var.setncattr('units', 'days since time')
    lt_var.setncattr('axis', 'v')
    lt_var[:] = data['lead_time'].values

    # ensemble members
    # ------------------
    ncfile.createDimension('ens_member', len(data['ens_member']))
    ens_mem_var = ncfile.createVariable('ens_member', intData_type, ('ens_member',), fill_value=-9999)
    ens_mem_var.setncattr('standard_name', 'ens_member')
    ens_mem_var.setncattr('long_name', 'ensemble member')
    ens_mem_var.setncattr('units', 'member id')
    ens_mem_var.setncattr('axis', 'u')
    ens_mem_var[:] = np.arange(1, len(data['ens_member'])+1)

    # time
    # ------
    ncfile.createDimension('time', len(data['time']))
    time_var = ncfile.createVariable('time', intData_type, ('time',), fill_value=-9999)
    time_var.setncattr('standard_name', 'time')
    time_var.setncattr('long_name', 'time')
    time_var.setncattr('time_standard', 'UTC+00:00')
    time_var.setncattr('axis', 't')

    #time_units_str = 'days since {} 00:00:00'.format(data.attrs['fcast_date'])
    time_units_str = f"{timestep_str} since {data.attrs['fcast_date']}"
    time_var.setncattr('units', time_units_str)
    time_var[:] = data['time'].values
    
    # Borrowing from create_empty_stfnc.m
    # Name Arrays
    v_type = ['q','pet','rain','swe','tmin','tmax','tave']
    v_type_long = ['streamflow','potential evapotranspiration','rainfall','snow water equivalent','minimum temperature','maximum temperature','average temperature']
    v_units = ['m3/s','mm','mm','mm','K','K','K']
    v_ttype = [3,2,2,2,5,5,5]
    v_ttype_name = ['averaged over the preceding interval','accumulated over the preceding interval','accumulated over the preceding interval',
    'point value recorded in the preceding interval','point value recorded in the preceding interval','averaged over the preceding interval']
        
    d_type = [None] * 4
    d_type_long = [None] * 4
    d_type[0] = 'der';  d_type_long[0] = 'derived (from observations)';
    
    if int(STF_nc_vers) ==1:
        d_type[1] = 'fcast'
        d_type_long[1] = 'forecast'
    elif int(STF_nc_vers) ==2:
        d_type[1] = 'fct'
        d_type_long[1] = 'forecast';
    else:
        raise Exception("Version not recognised: Currently only version 1.X or 2.X are supported")
            
    d_type[2] = 'obs'
    d_type_long[2] = 'observed'
    d_type[3] = 'sim'
    d_type_long[3] = 'simulated';
    
    # change var_type and data_type to python based index starting from 0
    var_type = var_type-1
    data_type = data_type-1
    #print(f"data_type: {data_type}")
    # Create prescribed variable names
    if int(STF_nc_vers) ==1:
        var_name_s = f"{v_type[var_type]}_{d_type[data_type]}"
        var_name_l = f"{d_type_long[data_type]} {v_type_long[var_type]}"
        if ens:
            var_name_s = f"{var_name_s}_ens"
            var_name_l = f"{var_name_l} ensemble"        
    else:
        var_name_attr = d_type[data_type]
        dat_type_description = d_type_long[data_type];
        if data_type in [0, 2]:
            #print("Obs")
            var_name_s = f"{v_type[var_type]}_obs"
            var_name_l = f"observed {v_type_long[var_type]}"
        else:
            print("Sim")
            var_name_s = f"{v_type[var_type]}_sim"
            var_name_l = f"simulated v_type_long[var_type]"        
               
    qsim_var = ncfile.createVariable(var_name_s, 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
    qsim_var.setncattr('standard_name', var_name_s)
    qsim_var.setncattr('long_name', var_name_l)
    qsim_var.setncattr('units', v_units[var_type])
      
    qsim_var.setncattr('type', v_ttype[var_type])
    qsim_var.setncattr('type_description', v_ttype_name[var_type])
    if int(STF_nc_vers) == 2:
        qsim_var.setncattr('dat_type', var_name_attr)
        qsim_var.setncattr('dat_type_description', dat_type_description)
        qsim_var.setncattr('location_type', 'Point') 
    else:
        qsim_var.setncattr('Location_type', 'Point') 

            
    qsim_var[:,:,:,:] = data.values[:]

   
    # Specify the quality variable
    if dataQual is not None:
        qu_var_name_s = f"{var_name_s}_qual"
        if int(STF_nc_vers) == 1:
            if data_type ==2:                
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'station', 'lead_time'), fill_value=-1)    
                qsim_qual_var[:,:,:] = dataQual.values[:]
            else:
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'station'), fill_value=-1)   
                qsim_qual_var[:,:] = dataQual.values[:]                
        else:
            qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'ens_member','station', 'lead_time'), fill_value=-1) 
            qsim_qual_var[:,:,:,:] = dataQual.values[:]
     
        qu_var_name_l = f"{var_name_l} data quality";
        
        qsim_qual_var.setncattr('standard_name', qu_var_name_s)
        qsim_qual_var.setncattr('long_name', qu_var_name_l)
        if 'quality_code' in dataQual.attrs.keys():        
            Quality_code  = dataQual.attrs['quality_code']
        else:
            Quality_code  = 'Quality codes'
        
        qsim_qual_var.setncattr('units', Quality_code)                
        # Write data
        
    # close file
    ncfile.close()
    



def write_nc_stf2_old(out_nc_file: str, data: xr.DataArray, var_type =  1, subarea_names = None, data_type = 3,
                STF_nc_vers = 2, ens = False, timestep = 'days', dataQual:xr.DataArray = None, overwrite=True,
                nc_title='',catchment='',inst='CSIRO Environment',comment='', source=''):
    
    
    
    subXCentroid = np.nan #145.149
    subYCentroid = np.nan #-37.393
    subArea = np.nan #.30.155
    intData_type = 'i4'
    #var_type    -   Integer specifying the variable, as follows:
    #                   1 - streamflow
    #                   2 - potential evapotranspiration
    #                   3 - rainfall
    #                   4 - snow water equivalent
    #                   5 - minimum temperature
    #                   6 - maximum temperature
    
    #data_type   -   Integer specifying the data type of the variable, as
    #                   follows:
    #                   1 - derived from observations
    #                   2 - forecast
    #                   3 - observed
    #                   4 - simulated
    if timestep in ['weeks', 'w', 'wk', 'week']:
        timestep_str = 'weeks'
    elif timestep in ['days', 'd', 'ds', 'day']:
        timestep_str = 'days'
    elif timestep in ['hours', 'h', 'hr', 'hour']:
        timestep_str = 'hours'
    elif timestep in ['minutes', 'm', 'min', 'minute']:
        timestep_str = 'minutes'
    elif timestep in ['seconds', 's', 'sec', 'second']:
        timestep_str = 'seconds'
    else:
        raise Exception(f"xr_open_dataset_fast has not been implemented for {timestep} unit") 
    
    if subarea_names is None:
        subarea_names = np.arange(1, len(data['station'])+1)
        subarea_names = [str(num) for num in subarea_names]
    # Check if file exists
    if os.path.exists(out_nc_file):
        if not overwrite:
            print(f"Warning: The file '{out_nc_file}' exists, so either set overwrite=True to overwrite or give new filename.")
            pass
        else:
            os.remove(out_nc_file)
            print(f"Warning: The file '{out_nc_file}' has been overwritten.")
    
    # Create netcdf file    
    ncfile = Dataset(out_nc_file, 'w', format='NETCDF4')
    # Global Attributes
    #ncfile.description = 'CCLIR forecasts'
    ncfile.history = 'Created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    
    ncfile.title = nc_title
    ncfile.institution = inst
    ncfile.source = source
    ncfile.catchment = catchment
    ncfile.STF_convention_version = STF_nc_vers
    ncfile.STF_nc_spec = 'https://wiki.csiro.au/display/wirada/NetCDF+for+SWIFT'
    ncfile.comment = comment
         
    #  station id etc.
    # --------------------
    ncfile.createDimension('station', len(subarea_names))
    station_var = ncfile.createVariable('station', intData_type, ('station',), fill_value=-9999)
    station_var[:] = np.arange(1, len(subarea_names)+1)

    station_id_var = ncfile.createVariable('station_id', intData_type, ('station',), fill_value=-9999)
    station_id_var.setncattr('long_name', 'station or node identification code')
    station_id_var[:] = [int(stn_name) for stn_name in subarea_names]

    ncfile.createDimension('strLen', 30)
    station_name_var = ncfile.createVariable('station_name', 'c', ('station', 'strLen'))
    station_name_var.setncattr('long_name', 'station or node name')
    for s_i, stn_name in enumerate(subarea_names):
        char_stn_name = [' '] * 30  # 30 char length
        char_stn_name[:len(stn_name)] = stn_name
        station_name_var[s_i, :] = char_stn_name

    # coordinates, area
    # --------------------
    lat_var = ncfile.createVariable('lat', 'f', ('station', ), fill_value=-9999)
    lat_var.setncattr('long_name', 'latitude')
    lat_var.setncattr('units', 'degrees_north')
    lat_var.setncattr('axis', 'y')
    lat_var[:] = subYCentroid

    lon_var = ncfile.createVariable('lon', 'f', ('station',), fill_value=-9999)
    lon_var.setncattr('long_name', 'longitude')
    lon_var.setncattr('units', 'degrees_east')
    lon_var.setncattr('axis', 'x')
    lon_var[:] = subXCentroid

    area_var = ncfile.createVariable('area', 'f', ('station',), fill_value=-9999)
    area_var[:] = subArea

    # lead time
    # ------------
    ncfile.createDimension('lead_time', len(data['lead_time']))
    lt_var = ncfile.createVariable('lead_time', intData_type, ('lead_time',), fill_value=-9999)
    lt_var.setncattr('standard_name', 'lead time')
    lt_var.setncattr('long_name', 'forecast lead time')
    lt_var.setncattr('units', 'days since time')
    lt_var.setncattr('axis', 'v')
    lt_var[:] = data['lead_time'].values

    # ensemble members
    # ------------------
    ncfile.createDimension('ens_member', len(data['ens_member']))
    ens_mem_var = ncfile.createVariable('ens_member', intData_type, ('ens_member',), fill_value=-9999)
    ens_mem_var.setncattr('standard_name', 'ens_member')
    ens_mem_var.setncattr('long_name', 'ensemble member')
    ens_mem_var.setncattr('units', 'member id')
    ens_mem_var.setncattr('axis', 'u')
    ens_mem_var[:] = np.arange(1, len(data['ens_member'])+1)

    # time
    # ------
    ncfile.createDimension('time', len(data['time']))
    time_var = ncfile.createVariable('time', intData_type, ('time',), fill_value=-9999)
    time_var.setncattr('standard_name', 'time')
    time_var.setncattr('long_name', 'time')
    time_var.setncattr('time_standard', 'UTC+00:00')
    time_var.setncattr('axis', 't')

    #time_units_str = 'days since {} 00:00:00'.format(data.attrs['fcast_date'])
    time_units_str = f"{timestep_str} since {data.attrs['fcast_date']}"
    time_var.setncattr('units', time_units_str)
    time_var[:] = data['time'].values
    
    # Borrowing from create_empty_stfnc.m
    # Name Arrays
    v_type = ['q','pet','rain','swe','tmin','tmax','tave']
    v_type_long = ['streamflow','potential evapotranspiration','rainfall','snow water equivalent','minimum temperature','maximum temperature','average temperature']
    v_units = ['m3/s','mm','mm','mm','K','K','K']
    v_ttype = [3,2,2,2,5,5,5]
    v_ttype_name = ['averaged over the preceding interval','accumulated over the preceding interval','accumulated over the preceding interval',
    'point value recorded in the preceding interval','point value recorded in the preceding interval','averaged over the preceding interval']
        
    d_type = [None] * 4
    d_type_long = [None] * 4
    d_type[0] = 'der';  d_type_long[0] = 'derived (from observations)';
    
    if int(STF_nc_vers) ==1:
        d_type[1] = 'fcast'
        d_type_long[1] = 'forecast'
    elif int(STF_nc_vers) ==2:
        d_type[1] = 'fct'
        d_type_long[1] = 'forecast';
    else:
        raise Exception("Version not recognised: Currently only version 1.X or 2.X are supported")
            
    d_type[2] = 'obs'
    d_type_long[2] = 'observed'
    d_type[3] = 'sim'
    d_type_long[3] = 'simulated';
    
    # change var_type and data_type to python based index starting from 0
    var_type = var_type-1
    data_type = data_type-1
    #print(f"data_type: {data_type}")
    # Create prescribed variable names
    if int(STF_nc_vers) ==1:
        var_name_s = f"{v_type[var_type]}_{d_type[data_type]}"
        var_name_l = f"{d_type_long[data_type]} {v_type_long[var_type]}"
        if ens:
            var_name_s = f"{var_name_s}_ens"
            var_name_l = f"{var_name_l} ensemble"        
    else:
        var_name_attr = d_type[data_type]
        dat_type_description = d_type_long[data_type];
        if data_type in [0, 2]:
            #print("Obs")
            var_name_s = f"{v_type[var_type]}_obs"
            var_name_l = f"observed {v_type_long[var_type]}"
        else:
            print("Sim")
            var_name_s = f"{v_type[var_type]}_sim"
            var_name_l = f"simulated v_type_long[var_type]"        
            
    # [time][ens_member][station][lead_time]
    # if forecast_var == 'streamflow':
        # qsim_var = ncfile.createVariable('q_sim', 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
        # qsim_var.setncattr('standard_name', 'q_sim')
        # qsim_var.setncattr('long_name', 'simulated streamflow')
        # qsim_var.setncattr('units', 'mm')
    # elif forecast_var == 'storage':
        # qsim_var = ncfile.createVariable('v_sim', 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
        # qsim_var.setncattr('standard_name', 'v_sim')
        # qsim_var.setncattr('long_name', 'simulated storage volume')
        # qsim_var.setncattr('units', 'ML')
    # elif forecast_var == 'rainfall':
        # qsim_var = ncfile.createVariable('rain_sim', 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
        # qsim_var.setncattr('standard_name', 'rain_sim')
        # qsim_var.setncattr('long_name', 'simulated rainfall')
        # qsim_var.setncattr('units', 'mm')
    qsim_var = ncfile.createVariable(var_name_s, 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
    qsim_var.setncattr('standard_name', var_name_s)
    qsim_var.setncattr('long_name', var_name_l)
    qsim_var.setncattr('units', v_units[var_type])
      
    qsim_var.setncattr('type', v_ttype[var_type])
    qsim_var.setncattr('type_description', v_ttype_name[var_type])
    if int(STF_nc_vers) == 2:
        qsim_var.setncattr('dat_type', var_name_attr)
        qsim_var.setncattr('dat_type_description', dat_type_description)
        qsim_var.setncattr('location_type', 'Point') 
    else:
        qsim_var.setncattr('Location_type', 'Point') 

         
    # qsim_var.setncattr('type', '2.0')
    # qsim_var.setncattr('type_description', 'accumulated over the preceding interval')
    # qsim_var.setncattr('dat_type', 'fct')
    # qsim_var.setncattr('dat_type_description', 'forecast data')
    # qsim_var.setncattr('location_type', 'Point')
    
    
    #qsim_var[0, :, :, :] = data.values[:]
    #tmp = data.values[:]
    #print(tmp.shape)
    qsim_var[:,:,:,:] = data.values[:]

   
    # Specify the quality variable
    if dataQual is not None:
        qu_var_name_s = f"{var_name_s}_qual"
        if int(STF_nc_vers) == 1:
            if data_type ==2:                
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'station', 'lead_time'), fill_value=-1)    
                qsim_qual_var[:,:,:] = dataQual.values[:]
            else:
                qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'station'), fill_value=-1)   
                qsim_qual_var[:,:] = dataQual.values[:]                
        else:
            qsim_qual_var = ncfile.createVariable(qu_var_name_s, 'f', ('time', 'ens_member','station', 'lead_time'), fill_value=-1) 
            qsim_qual_var[:,:,:,:] = dataQual.values[:]
     
        qu_var_name_l = f"{var_name_l} data quality";
        
        qsim_qual_var.setncattr('standard_name', qu_var_name_s)
        qsim_qual_var.setncattr('long_name', qu_var_name_l)
        qsim_qual_var.setncattr('units', 'Quality codes')                
        # Write data
        
    # close file
    ncfile.close()
    
def writeDataToNcFileSTF2(outNcFile, subXCentroid, subYCentroid, subArea, locName, varValsFct, varValsObs, varValsOrders, leadTimes, ensNum):
    # Copy from Seline
    
    from datetime import datetime

    from netCDF4 import Dataset

    ncfile = Dataset(outNcFile, 'w', format='NETCDF4')
    ncfile.description = 'Estimation of {} diversions from orders'.format(locName)
    ncfile.history = 'Created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #  station id etc.
    # --------------------
    ncfile.createDimension('station', 1)
    station_var = ncfile.createVariable('station', 'i', ('station',), fill_value=-9999)
    station_var[:] = 1

    station_id_var = ncfile.createVariable('station_id', 'i', ('station',), fill_value=-9999)
    station_id_var.setncattr('long_name', 'station or node identification code')
    station_id_var[:] = 0

    ncfile.createDimension('strLen', 30)
    station_name_var = ncfile.createVariable('station_name', 'c', ('station', 'strLen'))
    station_name_var.setncattr('long_name', 'station or node name')
    if len(locName) <= 30: station_name_var[:] = '{:<30}'.format(locName) #30 char length
    if len(locName) > 30: station_name_var[:] = locName[:30]

    # coordinates, area
    # --------------------
    lat_var = ncfile.createVariable('lat', 'f', ('station', ), fill_value=-9999)
    lat_var.setncattr('long_name', 'latitude')
    lat_var.setncattr('units', 'degrees_north')
    lat_var.setncattr('axis', 'y')
    lat_var[:] = subYCentroid

    lon_var = ncfile.createVariable('lon', 'f', ('station',), fill_value=-9999)
    lon_var.setncattr('long_name', 'longitude')
    lon_var.setncattr('units', 'degrees_east')
    lon_var.setncattr('axis', 'x')
    lon_var[:] = subXCentroid

    area_var = ncfile.createVariable('area', 'f', ('station',), fill_value=-9999)
    area_var[:] = subArea

    # lead time
    # ------------
    ncfile.createDimension('lead_time', len(leadTimes))
    lt_var = ncfile.createVariable('lead_time', 'i', ('lead_time',), fill_value=-9999)
    lt_var.setncattr('standard_name', 'lead time')
    lt_var.setncattr('long_name', 'forecast lead time')
    lt_var.setncattr('units', 'hours since time')
    lt_var.setncattr('axis', 'v')
    lt_var[:] = range(1,len(leadTimes)+1)

    # ensemble members
    # ------------------
    ncfile.createDimension('ens_member', ensNum)
    ens_mem_var = ncfile.createVariable('ens_member', 'i', ('ens_member',), fill_value=-9999)
    ens_mem_var.setncattr('standard_name', 'ens_member')
    ens_mem_var.setncattr('long_name', 'ensemble member')
    ens_mem_var.setncattr('units', 'member id')
    ens_mem_var.setncattr('axis', 'u')
    ens_mem_var[:] = range(1,ensNum+1)

    # time
    # ------
    ncfile.createDimension('time', 1)
    time_var = ncfile.createVariable('time', 'i', ('time',), fill_value=-9999)
    time_var.setncattr('standard_name', 'time')
    time_var.setncattr('long_name', 'time')
    time_var.setncattr('time_standard', 'UTC+00:00')
    time_var.setncattr('axis', 't')
    time_var[:] = 0

    issDt = leadTimes[0]-relativedelta(hours=1)
    time_units_str = 'hours since {:04d}-{:02d}-{:02d} {:02d}:00:00'.format(issDt.year, issDt.month, issDt.day, issDt.hour, issDt.minute, issDt.second)
    time_var.setncattr('units', time_units_str)

    # data of interest, forecast
    # --------------------------------
    # [time=1][ens_member][station=1][lead_time]
    varData = ncfile.createVariable('diversion_fct', 'f', ('time', 'ens_member', 'station', 'lead_time'), fill_value=-9999)
    varData.setncattr('standard_name', 'diversion_fct')
    varData.setncattr('long_name', 'estimated flow diversion')
    varData.setncattr('units', 'ML/hour')
    varData.setncattr('type_description', 'average over the preceding interval')
    varData[0, :, 0, :] = varValsFct #varValsFct in [ensMember][leadTime]

    # data of interest, actual observed
    # ----------------------------------
    # [time=1][station=1][lead_time]
    varObs = ncfile.createVariable('diversion_obs', 'f', ('time', 'station', 'lead_time'), fill_value=-9999)
    varObs.setncattr('standard_name', 'diversion_obs')
    varObs.setncattr('long_name', 'actual flow diversion')
    varObs.setncattr('units', 'ML/hour')
    varObs.setncattr('type_description', 'average over the preceding interval')
    varObs[0, 0, :] = varValsObs  #varValsObs in [leadTime]

    # data of interest, orders, predictor
    # --------------------------------------
    # [time=1][station=1][lead_time]
    varOrders = ncfile.createVariable('order', 'f', ('time', 'station', 'lead_time'), fill_value=-9999)
    varOrders.setncattr('standard_name', 'order')
    varOrders.setncattr('long_name', 'order')
    varOrders.setncattr('units', 'ML/hour')
    varOrders.setncattr('type_description', 'average over the preceding interval')
    varOrders[0, 0, :] = varValsOrders  #varValsOrders in [leadTime]

    ncfile.close()

