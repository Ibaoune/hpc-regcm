# SRC_REGCM / scripts / download_data

**Overview**:
Contains automated bash scripts designed to interface with external climate data repositories (like ECMWF or ICTP servers) to download the necessary global forcing datasets required to run RegCM.

**Files**:
- **`ein15.sh`**: Script to download ERA-Interim reanalysis data at 1.5-degree resolution, providing the atmospheric boundary conditions.
- **`clm.sh` & `clm45.sh`**: Scripts to download Community Land Model (CLM) specific input datasets (vegetation types, soil types) required for the land-surface interactions in RegCM.
- **`sst.sh`**: Script to download weekly or monthly Sea Surface Temperature boundary conditions.
- **`sd.sh`**: Script to download Surface Data (e.g., topography, land use, snow depth) required by the `terrain` pre-processing step.
