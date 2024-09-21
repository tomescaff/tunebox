"""Script to create the dataset with the modeled data for the period 1976-2004

This script reads the modeled data from the CMIP5 models at the closest grid
point to Quinta Normal and creates a netcdf file with the modeled data for the 
period 1976-2004. The script reads the precipitation, geopotential height at 
700 hPa and temperature at 700 hPa, and calculates the geopotential height at 
which the temperature is 0 ºC using a 6.5ºC/km lapse rate. 
"""

import yaml
import glob
import xarray as xr
import numpy as np
import pandas as pd

# read models metadata
with open("info_models_historical.yml") as stream:
    data = yaml.safe_load(stream)

models = list(data['models'].keys())

# Quinta Normal default location 
lat=-33.44
lon=289.35

# declare lists to store data
pr_list = []
z700_list = []
t700_list = []

# calendar with non-leap days
time = pd.date_range('1976-01-01', '2004-12-31', freq='1D')
time = time[(time.day != 29) | (time.month != 2)]

# read precipitation
for model in models:
    ini_fn = data['models'][model]['pr']['ini']
    end_fn = data['models'][model]['pr']['end']
    
    basedir = '/mnt/cirrus/cmip5_fromtape/recovery/historical/day/pr/'
    basedir += f'{model}/r1i1p1'
    ini_fp = f'{basedir}/{ini_fn}'
    end_fp = f'{basedir}/{end_fn}'
    
    fps = sorted(glob.glob(f'{basedir}/*.nc'))
    ini_idx = fps.index(ini_fp)
    end_idx = fps.index(end_fp)
    
    ds = xr.open_mfdataset(fps[ini_idx:end_idx+1], combine='by_coords')
    pr = ds[data['models'][model]['pr']['name']]
    pr = pr.sel(time=slice('1976-01-01', '2004-12-31'))
    pr = pr.sel(lat=lat, lon=lon, method='nearest').squeeze()
    bool_siunits = data['models'][model]['pr']['units'] == 'kgm-2s-1'
    pr = pr * 86400 if bool_siunits else pr * 86400
    pr = pr.sel(time=~((pr.time.dt.month == 2) & (pr.time.dt.day == 29)))
    pr = xr.DataArray(pr.values, coords={'time': time}, dims=['time'])
    pr_list = pr_list + [pr.expand_dims(dim={'model': [model]}, axis=0)]

pr_da = xr.concat(pr_list, dim='model')


# read geopotential height at 700 hPa
for model in models:
    ini_fn = data['models'][model]['zg']['ini']
    end_fn = data['models'][model]['zg']['end']
    
    basedir = '/mnt/cirrus/cmip5_fromtape/recovery/historical/day/zg/'
    basedir += f'{model}/r1i1p1'
    ini_fp = f'{basedir}/{ini_fn}'
    end_fp = f'{basedir}/{end_fn}'
    
    fps = sorted(glob.glob(f'{basedir}/*.nc'))
    ini_idx = fps.index(ini_fp)
    end_idx = fps.index(end_fp)
    
    ds = xr.open_mfdataset(fps[ini_idx:end_idx+1], combine='by_coords')
    zg = ds[data['models'][model]['zg']['name']]
    zg = zg.sel(time=slice('1976-01-01', '2004-12-31'))
    zg = zg.sel(lat=lat, lon=lon, method='nearest').squeeze()
    zg = zg * 1 if data['models'][model]['zg']['units'] == 'm' else zg * 1  
    zg = zg.sel(time=~((zg.time.dt.month == 2) & (zg.time.dt.day == 29)))
    z700 = zg.sel(plev=70000).squeeze()
    z700 = xr.DataArray(z700.values, coords={'time': time}, dims=['time'])
    z700_list = z700_list + [z700.expand_dims(dim={'model': [model]}, axis=0)]

z700_da = xr.concat(z700_list, dim='model')

# read temperature at 700 hPa
for model in models:
    ini_fn = data['models'][model]['ta']['ini']
    end_fn = data['models'][model]['ta']['end']
    
    basedir = '/mnt/cirrus/cmip5_fromtape/recovery/historical/day/ta/'
    basedir += f'{model}/r1i1p1'
    ini_fp = f'{basedir}/{ini_fn}'
    end_fp = f'{basedir}/{end_fn}'
    
    fps = sorted(glob.glob(f'{basedir}/*.nc'))
    ini_idx = fps.index(ini_fp)
    end_idx = fps.index(end_fp)
    
    ds = xr.open_mfdataset(fps[ini_idx:end_idx+1], combine='by_coords')
    ta = ds[data['models'][model]['ta']['name']]
    ta = ta.sel(time=slice('1976-01-01', '2004-12-31'))
    ta = ta.sel(lat=lat, lon=lon, method='nearest').squeeze()
    ta = ta * 1 if data['models'][model]['zg']['units'] == 'm' else ta * 1 
    ta = ta.sel(time=~((ta.time.dt.month == 2) & (ta.time.dt.day == 29))) 
    t700 = ta.sel(plev=70000).squeeze()
    t700 = xr.DataArray(t700.values, coords={'time': time}, dims=['time'])
    t700_list = t700_list + [t700.expand_dims(dim={'model': [model]}, axis=0)]

t700_da = xr.concat(t700_list, dim='model')

# compute H0
dt_dz = -6.5*1e-3 # ºC/m
H0 = (273.15 - t700_da)/dt_dz + z700_da

# save data
out_fp = '/home/tcarrasco/result/data/floods/mod_QN_CMIP5_1976_2004.nc'
ds = xr.Dataset({'pr': pr_da, 'z700': z700_da, 't700': t700_da, 'H0': H0})
ds.to_netcdf(out_fp)





