# Precipitation Intensity Distributions (PDFs)

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

## Execution Examples (Via SLURM)
```bash
# Submit Hourly PDF post-processing
sbatch slurm/postproc_hourly_precip.sbatch 2000

# Submit Daily Station PDF post-processing
sbatch slurm/postproc_daily_station.sbatch 2001
```

## Current Contents
- `pr_daily_pdf_insitu_20000101_20010831.png`
- `pr_hourly_pdf_common_grid_20000101_20010831.png`
- `pr_hourly_pdf_native_resolution_20000101_20010831.png`
- `pr_station_intensity_20000101_20010831.csv`

---
*Note: This README is automatically generated and updated via `src/commun/11_generate_readmes.py`.*
