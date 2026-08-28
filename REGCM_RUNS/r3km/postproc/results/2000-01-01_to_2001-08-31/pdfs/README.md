# Precipitation Intensity Distributions (PDFs)

**Author:** M. El Aabaribaoune (@um6p)

## Scientific Purpose
This directory contains normalized Probability Density Functions (PDFs) of precipitation intensity.

### Daily station-scale precipitation distribution
RegCM precipitation sampled at rain-gauge locations compared against in-situ observations using common station-days. 
A wet-day threshold of PR $\ge$ 0.1 mm day⁻¹ is strictly applied to both datasets to ensure identical sampling populations. 
Files are named `pr_daily_pdf_insitu_YYYY.png`.

### Hourly native-resolution precipitation distribution
RegCM (~3 km) vs native ERA5 (~31 km).
This diagnostic is explicitly scale-dependent. 
A wet-hour threshold of PR $\ge$ 0.1 mm h⁻¹ is applied. 
Files are named `pr_hourly_pdf_native_resolution_YYYY.png`.

### Hourly common-grid precipitation distribution
RegCM aggregated to ERA5 scale before comparison.
This is the preferred like-for-like hourly intensity comparison. 
Files are named `pr_hourly_pdf_common_grid_YYYY.png`.

## Methodology & Data Details
- **Scripts Used**: 
  - `src/pdfs/04_hourly_precip_pdf.py` for hourly resolution.
  - `src/pdfs/08_daily_station_pdf.py` for daily station resolution.
- **Data Files Used**: 
  - RegCM Output: `*SHF*.nc` (for hourly) and `*STS*.nc` (for daily accumulations) from `archive_periods`.
  - Reference Data: ERA5 (~31km) for hourly grids, and In-Situ Stations (ABH configuration) for daily points.
- **Variables**: `pr` (Precipitation)
- **Units**: 
  - Hourly intensity: mm/h (wet-hour threshold $\ge$ 0.1 mm h⁻¹)
  - Daily intensity: mm/day (wet-day threshold $\ge$ 0.1 mm day⁻¹)

## Execution Examples (Via SLURM)
```bash
# Submit Hourly PDF post-processing
sbatch slurm/postproc_hourly_precip.sbatch 2000-01-01 2001-08-31

# Submit Daily Station PDF post-processing
sbatch slurm/postproc_daily_station.sbatch 2000-01-01 2001-08-31
```

## Current Contents
- `pr_daily_pdf_insitu_20000101_20010831.png`
- `pr_hourly_pdf_common_grid_20000101_20010831.png`
- `pr_hourly_pdf_native_resolution_20000101_20010831.png`
- `pr_station_intensity_20000101_20010831.csv`


