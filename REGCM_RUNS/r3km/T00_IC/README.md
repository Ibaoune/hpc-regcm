# T00_IC: Pre-processing & Initial Conditions

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
This phase is responsible for taking raw global boundary conditions (like ERA-Interim, SST) and interpolating them onto the 3 km Morocco grid to create the Initial Conditions (IC) and Boundary Conditions (BC).

**Files**:
- **`job_createInitialState.sh`**: The SLURM batch script that allocates cluster resources (nodes/cores) and sequentially executes the RegCM pre-processing binaries (`terrain`, `sst`, `icbc`) to generate the initial surface, sea surface, and atmospheric conditions.
- **`test_0010.in`**: The namelist configuration file specific to the IC/BC generation. It defines the grid dimensions, domain center, projection, and the temporal span for the initial state generation.
- **`bin`**: A symbolic link pointing to the `SRC_REGCM/bin` directory, giving local scripts access to the compiled RegCM pre-processing executables.

**Structure**:
- **`input/`**: Directory where raw global datasets are staged before interpolation.
