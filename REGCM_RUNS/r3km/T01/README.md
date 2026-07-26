# T01: Main Production Run

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
This is the core working directory for the actual execution of the RegCM climate model (model integration) at the 3 km resolution. It contains the execution logic, the main physics configuration, and automation scripts for continuous chaining.

**Files**:
- **`job.sh`**: The SLURM job submission script. It loads necessary modules (GCC, OpenMPI, NetCDF), sets up the environment, and launches the `regcmMPI` executable using `mpirun` across 8 compute nodes.
- **`run_chain.py`**: A robust Python automation script. It is designed to read the model's progress, update the namelist to the next chronological simulation period, and automatically submit the next SLURM job so the simulation runs continuously without manual intervention.
- **`test_0010.in`**: The primary RegCM namelist file. It defines the physical parameterizations (e.g., PBL scheme, Cumulus convection, Radiation), output frequencies, and time-step controls for the model run.
- **`chain_state.txt`**: A small state-tracking text file updated by `run_chain.py` to maintain the current date/period of the simulation to prevent job overlap.
- **`bin`**: A symbolic link pointing to `SRC_REGCM/bin`, providing access to the compiled `regcmMPI` binary.

**Structure**:
- **`doc/`**: Contains report generation scripts and documentation.
- **`input/`**: Processed initial conditions from T00_IC.
- **`output/`**: NetCDF model output results.
- **`logs/`**: SLURM output/error logs.
- **`archive_periods/`**: Cold storage for completed simulation periods.
- **`templates/`**: Template files used by `run_chain.py`.
