# Metrics Results

**Author:** M. El Aabaribaoune (@um6p)

**Directory**: `postproc/results/metrics`

## Methodology & Data Details
- **Script Used**: Computed automatically by `src/maps/03_climatology_maps.py` during the map generation process.
- **Data Files Used**: 
  - RegCM Output: `*STS*.nc` (for Precipitation) and `*SRF*.nc` (for Temperature) from `archive_periods`.
  - Reference Data: MSWEP (Precipitation) and CPC (Temperature).
- **Variables**: `pr` (Precipitation), `tasmax` (Maximum Surface Air Temperature), `tasmin` (Minimum Surface Air Temperature).
- **Units**: 
  - `pr`: mm/day
  - `tasmax` / `tasmin`: °C

## Current Contents
- `climatology_metrics_*.csv`
