# T01: Main Production Simulation

This is the core working directory for the main 3 km RegCM production run. It includes:
- **`job.sh`**: The SLURM job script for launching the MPI simulation.
- **`test_0010.in`**: The primary namelist configuration file defining the model physics and domain.
- **`run_chain.py`**: A Python automation script for chaining multiple continuous runs seamlessly.
- **`doc/`**: Scripts for automatically generating progress reports.
Output and input data files are generated in the `output/` and `input/` folders (which are untracked by Git).
