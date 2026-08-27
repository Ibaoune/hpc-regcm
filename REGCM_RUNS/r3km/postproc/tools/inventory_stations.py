#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import pandas as pd
import numpy as np
from pathlib import Path

csv_file = '/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/TEAM/data/Observed_data/ABH_stations_plusziz_and_abhbc1.csv'
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

print("Reading CSV...")
df = pd.read_csv(csv_file)
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year

# Look for various missing value indicators
missing_vals = [-999, -9999, 999, 9999]
df.replace(missing_vals, np.nan, inplace=True)
df.replace('', np.nan, inplace=True)
df.replace(' ', np.nan, inplace=True)

stations = df['Station'].nunique()
date_min = df['Date'].min()
date_max = df['Date'].max()

df_2000_2004 = df[(df['Year'] >= 2000) & (df['Year'] <= 2004)]
stations_2000_2004 = df_2000_2004['Station'].nunique()

# Variables present
vars_present = [c for c in df.columns if c not in ['Date', 'Station', 'Year', 'Latitude', 'Longitude', 'Elevation']]

# Stats per station
stats = []
for st, grp in df.groupby('Station'):
    st_dict = {
        'Station': st,
        'Lat': grp['Latitude'].iloc[0] if 'Latitude' in df.columns else np.nan,
        'Lon': grp['Longitude'].iloc[0] if 'Longitude' in df.columns else np.nan,
        'Elev': grp['Elevation'].iloc[0] if 'Elevation' in df.columns else np.nan,
        'Start': grp['Date'].min().strftime('%Y-%m-%d'),
        'End': grp['Date'].max().strftime('%Y-%m-%d'),
        'Records': len(grp)
    }
    
    if 'Precipitation' in df.columns:
        pr_vals = grp['Precipitation']
        st_dict['PR_Missing_%'] = pr_vals.isna().mean() * 100
        st_dict['PR_Zeros_%'] = (pr_vals == 0.0).mean() * 100
        
    stats.append(st_dict)

stats_df = pd.DataFrame(stats)
csv_path = REPORTS_DIR / "insitu_station_availability.csv"
stats_df.to_csv(csv_path, index=False)

with open(REPORTS_DIR / "insitu_inventory.md", 'w') as f:
    f.write("# In-Situ Stations Inventory\\n\\n")
    f.write(f"- **Total stations**: {stations}\\n")
    f.write(f"- **Stations (2000-2004)**: {stations_2000_2004}\\n")
    f.write(f"- **Period**: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}\\n")
    f.write(f"- **Variables**: {', '.join(vars_present)}\\n")
    if 'Latitude' in df.columns:
        f.write(f"- **Lat range**: {df['Latitude'].min():.2f} to {df['Latitude'].max():.2f}\\n")
        f.write(f"- **Lon range**: {df['Longitude'].min():.2f} to {df['Longitude'].max():.2f}\\n")
    
    if 'Precipitation' in df.columns:
        glob_miss = df['Precipitation'].isna().mean()*100
        glob_zero = (df['Precipitation']==0).mean()*100
        f.write(f"- **Global Missing PR**: {glob_miss:.2f}%\\n")
        f.write(f"- **Global Zero PR**: {glob_zero:.2f}%\\n")

print("Generated insitu_inventory.md and insitu_station_availability.csv")
