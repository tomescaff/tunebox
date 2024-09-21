import pandas as pd
import xarray as xr
import numpy as np

# read observed data at Quinta Normal station
filepath = '/home/tcarrasco/result/data/QN/QN_daily_precip.csv'
df = pd.read_csv(filepath, parse_dates={'time': ['agno', ' mes', ' dia']}, )
df = df.set_index('time')
da = df[' valor'].to_xarray()
da = da.sel(time=slice('1979-01-01', '2004-12-31'))

# fill absent data with nan
dr = pd.date_range(start='1976-01-01', end='2004-12-31', freq='D')
pr = xr.DataArray(np.nan, coords=[dr], dims=['time'])
for t in da.time:
    pr.loc[t] = da.sel(time=t)

# read ERA5 data at Quinta Normal station
basedir_z500 = '/home/tcarrasco/data_era5/z_500/'
basedir_t500 = '/home/tcarrasco/data_era5/t_500/'

dr_m = pd.date_range(start='1979-01-01', end='2004-12-31', freq='M')
z500 = xr.DataArray(np.nan, coords=[dr], dims=['time'])
t500 = xr.DataArray(np.nan, coords=[dr], dims=['time'])

for i in range(dr_m.size):
    year = dr_m[i].year
    month = dr_m[i].month
    
    # read z500 data
    filename = f'ERA5_z500_6h_{year:04d}_{month:02d}_Global_025deg.nc'
    fp_z500 = basedir_z500 + filename
    ds_z500 = xr.open_dataset(fp_z500)
    da_z500 = ds_z500['z'].sel(latitude=-33.5, longitude=-70.5, 
                               method='nearest')
    da_z500 = da_z500/9.8
    da_z500 = da_z500[2::4]
    
    #read t500 data
    filename = f'ERA5_t500_6h_{year:04d}_{month:02d}_Global_025deg.nc'
    fp_t500 = basedir_t500 + filename
    ds_t500 = xr.open_dataset(fp_t500)
    da_t500 = ds_t500['t'].sel(latitude=-33.5, longitude=-70.5, 
                               method='nearest')
    da_t500 = da_t500[2::4]
    
    for t in da_z500.time:
        z500.loc[t] = da_z500.sel(time=t)
        t500.loc[t] = da_t500.sel(time=t)

# compute ISO0C height
dt_dz = -6.5*1e-3 # ºC/m

# (t2 - t1)/(z2 - z1) = dt_dz
# t2 = t1 + dt_dz * (z2 - z1)
# z2 = (t2 - t1)/dt_dz + z1
H0 = (273.15 - t500)/dt_dz + z500

# save data
out_fp = '/home/tcarrasco/results/data/floods/obs_QN_ERA5_1976_2004.nc'
dsout = xr.Dataset({'pr': pr, 'z500': z500, 't500': t500, 'H0': H0})
dsout.to_netcdf(out_fp)    
    



