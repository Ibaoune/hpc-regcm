#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import os
import glob
import netCDF4 as nc
import cftime
import pandas as pd
from pathlib import Path

TEAM_DATA = "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data"
R3KM_DATA = "/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/users/mohammad.elaabaribao/RegCM/REGCM_RUNS/r3km/data"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Define where to look
SEARCH_PATHS = [
    {"name": "CHIRPS", "path": f"{TEAM_DATA}/Observed_data/CHIRPS", "location": "TEAM_SHARED_DATA"},
    {"name": "CHIRPS", "path": f"{R3KM_DATA}/CHIRPS", "location": "LOCAL_TEST_DATA"},
    {"name": "CPC", "path": f"{TEAM_DATA}/CPC", "location": "TEAM_SHARED_DATA"},
    {"name": "CPC", "path": f"{R3KM_DATA}/CPC", "location": "LOCAL_TEST_DATA"},
    {"name": "MSWEP", "path": f"{TEAM_DATA}/mswep", "location": "TEAM_SHARED_DATA"},
    {"name": "ERA5", "path": f"{TEAM_DATA}/ERA5", "location": "TEAM_SHARED_DATA"},
    {"name": "GLEAM", "path": f"{TEAM_DATA}/GLEAM", "location": "TEAM_SHARED_DATA"},
]

def analyze_dataset():
    results = []
    
    for entry in SEARCH_PATHS:
        dataset_name = entry["name"]
        base_path = entry["path"]
        location = entry["location"]
        
        if not os.path.exists(base_path):
            continue
            
        files = glob.glob(f"{base_path}/**/*.nc", recursive=True) + glob.glob(f"{base_path}/**/*.nc4", recursive=True)
        if not files: continue
        
        # Group files by the main variables they contain
        var_groups = {}
        for f in files:
            try:
                with nc.Dataset(f) as ds:
                    # Ignore coordinate variables
                    main_vars = [v for v in ds.variables.keys() if v not in ['lat','lon','latitude','longitude','time','time_bnds','bounds_lat','bounds_lon','lon_bnds','lat_bnds']]
                    if not main_vars: continue
                    # Take the first main variable as representative for grouping
                    var = main_vars[0]
                    if var not in var_groups:
                        var_groups[var] = []
                    var_groups[var].append(f)
            except:
                pass
                
        for var, group_files in var_groups.items():
            group_files = sorted(group_files)
            
            # Read spatial info from first file
            try:
                with nc.Dataset(group_files[0]) as ds:
                    lat_var = ds.variables.get('lat', ds.variables.get('latitude'))
                    lon_var = ds.variables.get('lon', ds.variables.get('longitude'))
                    if lat_var is None or lon_var is None: continue
                    lat = lat_var[:]
                    lon = lon_var[:]
                    
                    time_var = ds.variables.get('time')
                    if time_var is not None:
                        dates = cftime.num2date(time_var[:], units=time_var.units, calendar=getattr(time_var, 'calendar', 'standard'))
                        start_date = str(dates[0]).split()[0]
                    else:
                        start_date = "UNKNOWN"
            except:
                continue
                
            # Read end date from last file
            try:
                with nc.Dataset(group_files[-1]) as ds:
                    time_last = ds.variables.get('time')
                    if time_last is not None:
                        dates_last = cftime.num2date(time_last[:], units=time_last.units, calendar=getattr(time_last, 'calendar', 'standard'))
                        end_date = str(dates_last[-1]).split()[0]
                    else:
                        end_date = "UNKNOWN"
            except:
                end_date = "UNKNOWN"
                
            lat_res = abs(lat[1]-lat[0]) if len(lat)>1 else 0
            
            lat_min, lat_max = float(lat.min()), float(lat.max())
            lon_min, lon_max = float(lon.min()), float(lon.max())
            
            # Normalize longitude to -180, 180 for coverage checking
            if lon_max > 180:
                norm_lon_min = lon_min - 360 if lon_min > 180 else lon_min
                norm_lon_max = lon_max - 360
                norm_lon_min, norm_lon_max = min(norm_lon_min, norm_lon_max), max(norm_lon_min, norm_lon_max)
            else:
                norm_lon_min, norm_lon_max = lon_min, lon_max
                
            # RegCM domain: lat 19.04 to 44.84, lon -32.37 to 7.22
            covers_regcm = (lat_min <= 19.04 and lat_max >= 44.84 and norm_lon_min <= -32.37 and norm_lon_max >= 7.22)
            # Morocco approx: lat 21.0 to 36.5, lon -18.0 to 1.5
            covers_morocco = (lat_min <= 21.0 and lat_max >= 36.5 and norm_lon_min <= -18.0 and norm_lon_max >= 1.5)
            covers_2000_2004 = (start_date <= "2000-01-01" and end_date >= "2004-12-31")
            
            results.append({
                "dataset": dataset_name,
                "variable": var,
                "location": location,
                "resolution": f"{lat_res:.2f} deg",
                "start_date": start_date,
                "end_date": end_date,
                "lat_min": f"{lat_min:.2f}",
                "lat_max": f"{lat_max:.2f}",
                "lon_min": f"{lon_min:.2f}",
                "lon_max": f"{lon_max:.2f}",
                "covers_full_regcm_domain": covers_regcm,
                "covers_morocco": covers_morocco,
                "covers_2000_2004": covers_2000_2004,
            })
            
    return results

if __name__ == "__main__":
    results = analyze_dataset()
    df = pd.DataFrame(results)
    
    csv_path = REPORTS_DIR / "dataset_inventory.csv"
    md_path = REPORTS_DIR / "dataset_inventory.md"
    df.to_csv(csv_path, index=False)
    
    md_str = "# RegCM Datasets Inventory\n\n"
    for idx, row in df.iterrows():
        md_str += f"### {row['dataset']} | {row['variable']} ({row['location']})\n"
        for col in df.columns:
            if col not in ['dataset', 'variable', 'location']:
                md_str += f"- **{col}**: {row[col]}\n"
        md_str += "\n"
        
    with open(md_path, 'w') as f:
        f.write(md_str)
        
    print(f"Generated {csv_path} and {md_path}")
