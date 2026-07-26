# SRC_REGCM: Adapted Source Code & Build Environment

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
This directory houses the highly customized version of the RegCM model source code (`RegCM-Toubkal`) that has been optimized for the Toubkal HPC architecture. It contains the code itself, environment files, and compilation scripts.

**Files**:
- **`arch_RegCM4.5_Tbkl.env`**: A crucial environment script that loads the exact GNU compiler, OpenMPI, NetCDF, and HDF5 modules required to build and run the model successfully on the cluster.
- **`compile_regcm.sh`**: A simple wrapper script that sources the environment and triggers the compilation process (`configure` and `make`).
- **`job.sh`**: A legacy or utility SLURM script related to testing the source code build process.

**Structure**:
- **`RegCM-4.5.0/`** (or `RegCM-Toubkal/`): The actual C/Fortran source code tree for the RegCM model.
- **`scripts/`**: Utility scripts for building the model and acquiring data.
- **`bin/`**: The destination directory for the compiled executables (`regcmMPI`, `terrain`, `icbc`, etc.). Ignored by Git.
