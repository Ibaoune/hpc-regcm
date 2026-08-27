#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
tools/test_plot_coordinates.py
==============================
Diagnostics for MSWEP and CPC coordinates to ensure cartopy plots them correctly.
"""

import sys
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import numpy as np
from pathlib import Path

def test_dataset_plot(name, path, var_name, lat_name, lon_name, extent=[-20, 5, 20, 40]):
    print(f"\n--- Testing {name} ---")
    print(f"Loading {path}...")
    try:
        ds = xr.open_dataset(path)
    except Exception as e:
        print(f"Failed to load {name}: {e}")
        return

    print("Variables:", list(ds.data_vars))
    
    # Get coordinates
    lat = ds[lat_name].values
    lon = ds[lon_name].values
    
    print(f"Lon shape: {lon.shape}, min: {lon.min()}, max: {lon.max()}")
    print(f"Lat shape: {lat.shape}, min: {lat.min()}, max: {lat.max()}")
    
    # Extract first timestep of variable
    data = ds[var_name].isel(time=0).values
    print(f"Data shape: {data.shape}")
    print(f"Data min: {np.nanmin(data)}, max: {np.nanmax(data)}, mean: {np.nanmean(data)}")

    # Plot
    fig = plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.set_extent(extent, crs=ccrs.PlateCarree())

    # If coordinates are 1D, we can use them directly in pcolormesh
    if lon.ndim == 1 and lat.ndim == 1:
        # Check if we need to meshgrid for plotting manually
        lon_m, lat_m = np.meshgrid(lon, lat)
    else:
        lon_m, lat_m = lon, lat

    print(f"Plotting with pcolormesh (shading='auto')...")
    pc = ax.pcolormesh(lon_m, lat_m, data, transform=ccrs.PlateCarree(), shading='auto', cmap='viridis')
    plt.colorbar(pc, ax=ax, label=var_name)
    ax.set_title(f"{name} Coordinate Test")
    
    out_dir = Path("results/qa")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"test_{name.lower()}_coords.png"
    plt.savefig(out_path, bbox_inches='tight', dpi=150)
    print(f"Saved test map to {out_path}")
    plt.close()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    test_dataset_plot(
        "CPC_tasmax", 
        "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/CPC/tasmax_CPC.nc",
        "tasmax", "lat", "lon"
    )
    
    test_dataset_plot(
        "MSWEP",
        "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/mswep/all_Mor/mswep_1979_2020.nc",
        "precipitation", "lat", "lon"
    )
