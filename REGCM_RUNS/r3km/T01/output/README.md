# T01 / output

**Overview**:
This is the primary destination directory for all variables calculated and outputted by the RegCM model run.

The model writes specialized NetCDF files here, categorized by physics components:
- **`*_ATM.*.nc`**: Atmospheric variables (Temperature, Wind, Pressure, etc.).
- **`*_SRF.*.nc`**: Surface variables (Precipitation, 2m Temperature, runoff).
- **`*_RAD.*.nc`**: Radiation variables (Shortwave/Longwave fluxes).
- **`*_SHF.*.nc`** & **`*_STS.*.nc`**: Sensible heat fluxes and surface temperature state files.

Because the model can generate up to 1.4 TB per simulated month, files here are frequently moved to `archive_periods/` and are fully ignored by Git.
