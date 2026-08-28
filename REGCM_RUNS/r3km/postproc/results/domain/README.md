# Domain Overview

**Author:** M. El Aabaribaoune (@um6p)

## Scientific Purpose
This diagnostic visualizes the geographic domain and configuration of the RegCM-Toubkal simulation. 
It confirms the model extent, resolution, and spatial bounds relative to the target study area (Morocco).

## Execution Example (Via SLURM)
```bash
sbatch slurm/postproc_domain.sbatch
```

## Methodology & Data Details
- **Script Used**: `src/domain/09_domain_overview.py`
- **Data Files Used**: 
  - RegCM Output: The first available `*STS*.nc` or `*SHF*.nc` file in the raw `archive_periods` directory to extract the native model grid and topography.
  - In-situ Data: Station coordinates loaded from the configured `ABH` dataset path in `configs/experiments/r3km_2000_2004.yaml`.
- **Variables**: `topo` (Elevation), `xlat` (Latitude), `xlon` (Longitude).
- **Units**: Elevation is in meters (m); coordinates are in degrees.

## Current Contents
- `regcm_r3km_domain_overview.png`
