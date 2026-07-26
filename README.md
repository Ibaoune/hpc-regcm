# RegCM Project - Regional Climate Modeling (Morocco)

**Author**: M. El Aabaribaoune (@um6p)

This repository hosts the runtime environment, configuration, and automation tools developed to perform high-resolution regional climate simulations over Morocco. It relies on the **RegCM** (v4.5) regional climate model and integrates specific developments to optimize its execution on the local HPC infrastructure (Toubkal cluster).

## Project Description

The primary objective is to simulate the climate of Morocco with a very fine spatial resolution of 3 km. The repository is structured to manage large volumes of data on a Lustre file system, and includes automated processing chains for launching, tracking, and producing simulation reports.

### Simulation Characteristics
- **Resolution**: 3.0 km (`ds = 3.0`)
- **Grid**: 920 x 1084 (`iy = 920`, `jx = 1084`), 50 vertical levels (`kz = 50`)
- **Domain Center**: Latitude 32.50 N (`clat`), Longitude -12.50 E (`clon`)
- **Projection**: Rotated Lat/Lon (`ROTLLR`)

---

## Component Distinction (Important)

This repository centralizes two types of components that must be clearly distinguished:

### 1. Adapted RegCM-Toubkal Source Code
The source code and executables of the RegCM model have been specially adapted for our architecture.
- **`SRC_REGCM/`**: Contains the adapted `RegCM-Toubkal` source code and environment scripts (`arch_RegCM4.5_Tbkl.env`, `compile_regcm.sh`) necessary for compiling the model on the Toubkal cluster. *Binaries and compiled objects are ignored in Git.*
- **Configuration**: The input files (`.in` such as `test_0010.in`) are specifically configured for our domains, but use the official RegCM format.

### 2. HPC Specific Extensions (Our Development)
These elements are the core of this GitHub repository. They are custom developments for our infrastructure to automate and manage simulations on the cluster:
- **Slurm Submission Scripts**: `job.sh` and `job_createInitialState.sh` files to allocate and use cluster nodes.
- **Python Automation Tools**: 
  - `run_chain.py`: Python automatic chaining script allowing the sequential submission of jobs over long periods without manual intervention.
- **Report Generation (`doc/`)**: Python scripts (`generate_report.py`, `generate_forcing_report.py`, etc.) to automatically generate detailed scientific reports (.md, .pdf) on the progress and validation of the simulations.
- **File Management**: Directory structure (`REGCM_RUNS/`) and purge system (via `.gitignore` and scripts) adapted to Lustre system constraints.

---

## Prerequisites and Dependencies

To use this environment on the HPC cluster, ensure you load the following modules:
- Compilers and MPI: **GCC**, **OpenMPI**
- Scientific libraries: **NetCDF**, **HDF5**
- Python Environment: **Python 3** (for executing `run_chain.py` and report generation)

---

## Directory Organization

```text
.
├── README.md                           # Main documentation (this file)
├── .gitignore                          # Git exclusions (large data files, logs)
├── REGCM_RUNS/                         # Main directory containing experiments
│   └── r3km/                           # Simulations at 3 km resolution
│       ├── T00_IC/                     # Initial conditions and forcings (input files)
│       └── T01/                        # Main production simulation
│           ├── job.sh                  # Main Slurm submission script
│           ├── run_chain.py            # Simulation chain automation tool
│           ├── test_0010.in            # Model configuration file
│           ├── doc/                    # Report generation tools (HPC specific)
│           ├── logs/                   # Slurm output logs
│           ├── archive_periods/        # Data archives by periods (ignored by Git)
│           ├── input/                  # Input data (content ignored by Git)
│           └── output/                 # Model results (content ignored by Git)
├── REGCM_GLOBEDAT/                     # Global input data (not versioned)
└── SRC_REGCM/                          # Official RegCM source code (not versioned)
```

---

## Installation and Usage Instructions

1. **Environment Preparation**
   Load the necessary modules on your HPC environment:
   ```bash
   module load gcc openmpi netcdf hdf5 python
   ```

2. **Generation of Initial Conditions**
   ```bash
   cd REGCM_RUNS/r3km/T00_IC
   sbatch job_createInitialState.sh
   ```

3. **Launching the Simulation**
   To run a single period:
   ```bash
   cd REGCM_RUNS/r3km/T01
   sbatch job.sh
   ```
   *Default allocated resources: 28 nodes x 32 tasks (896 MPI cores).*

4. **Automation (Period Chaining)**
   To run the simulation continuously by chaining periods:
   ```bash
   python3 run_chain.py
   ```

---

## Best Practices and Alerts

- **Disk Space**: The file writing frequency generates approximately **1.4 TB per simulated month** (`srffrq = 1.0`). Carefully monitor your Lustre quota.
- **Git**: The `.gitignore` file is strictly configured to block large files (`.nc`, `.grib`, `.tar`, etc.). **Never force** the addition of these data files into the repository. Only tool source code and configurations should be tracked.
- **Cleanup**: Regularly purge `logs/` directories and transfer files from the `output/` section to cold storage if necessary.
