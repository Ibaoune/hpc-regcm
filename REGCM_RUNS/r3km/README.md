# r3km Simulation Domain

**Author**: M. El Aabaribaoune (@um6p)

**Overview**: 
This directory holds the complete pipeline for the 3 km spatial resolution climate simulation over Morocco.

**Structure**:
- **`T00_IC/`**: The initial conditions and boundary conditions (ICBC) generation phase.
- **`T01/`**: The main production run phase (model integration).
- **`data/`**: Cleaned and subsetted observation data (CHIRPS, CPC, GPCP) for the year 2000, used for model validation.
- **`postproc/`**: The post-processing and validation framework.
