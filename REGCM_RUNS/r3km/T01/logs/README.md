# T01 / logs

**Author**: M. El Aabaribaoune (@um6p)

**Overview**:
This directory captures the `stdout` and `stderr` streams from SLURM during job execution.

**Files**:
- **`RegCM_Mor_28nds_*_SUCCESS.log`** / **`.out`** / **`.err`**: These files track the step-by-step console output of `regcmMPI`. They are vital for debugging model crashes, verifying loaded environment modules, and tracking the speed (time-steps per second) of the simulation.

Logs can accumulate quickly and are ignored by Git to keep the repository clean.
