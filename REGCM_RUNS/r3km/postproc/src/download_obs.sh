#!/bin/bash
set -euo pipefail

OBS_DIR="/home/mohammad.elaabaribao/lustre/climat-um6p-st-iwri-7ksifkvwkuy/users/mohammad.elaabaribao/RegCM/REGCM_RUNS/r3km/postproc/data/obs_raw"
mkdir -p "$OBS_DIR/CPC" "$OBS_DIR/CHIRPS" "$OBS_DIR/GPCC"

echo "Downloading CPC tasmax/tasmin (Global) for 2000..."
wget -q --show-progress -nc "https://downloads.psl.noaa.gov/Datasets/cpc_global_temp/tmax.2000.nc" -P "$OBS_DIR/CPC/"
wget -q --show-progress -nc "https://downloads.psl.noaa.gov/Datasets/cpc_global_temp/tmin.2000.nc" -P "$OBS_DIR/CPC/"

echo "Downloading CHIRPS precipitation (Daily, 0.05deg) for 2000..."
for month in $(seq -w 1 12); do
  wget -q --show-progress -nc "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/chirps-v2.0.2000.${month}.days_p05.nc" -P "$OBS_DIR/CHIRPS/"
done

echo "Merging CHIRPS monthly files into a single yearly file..."
module load CDO/2.0.5-gompi-2021b
cdo -O mergetime "$OBS_DIR/CHIRPS"/chirps-v2.0.2000.*.days_p05.nc "$OBS_DIR/CHIRPS/chirps_2000.nc"

echo "Downloads complete."
