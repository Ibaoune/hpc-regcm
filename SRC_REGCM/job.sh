#!/bin/bash
# Author: M. El Aabaribaoune (@um6p)
#
# Description:
# This SLURM batch script is used to run a regional climate model simulation 
# using RegCM (Regional Climate Model) in a high-performance computing (HPC) 
# environment at UM6P (Toubkal cluster). The simulation runs in parallel using 
# 8 compute nodes via MPI. The script sets up the required environment by 
# loading the necessary software modules (GCC, OpenMPI, NetCDF, HDF5, etc.), 
# logs system and environment information for reproducibility, and executes 
# the RegCM model with the specified input file. Output and error logs are 
# stored in a file named based on the SLURM job ID.

######################
## TOUBKAL    UM6P ##
######################
#SBATCH --job-name=RegCM01        # Job Name
#SBATCH --output=RegCM01_%j.log    # standard output
#SBATCH --error=RegCM01_%j.log    # error output
#SBATCH --nodes=8
#SBATCH --time=24:00:00             # Wall clock limit (minutes)
#SBATCH --account=CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU
# Display executed commands
set -x

OUT_FILE="RegCM01_${SLURM_JOB_ID}.log"

# Load necessary modules
module purge
module load GCC/11.2.0
module load OpenMPI/4.1.1-GCC-11.2.0
module load netCDF/4.8.1-gompi-2021b
module load HDF5/1.12.1-gompi-2021b
module load netCDF-Fortran/4.5.3-gompi-2021b
module load libtool/2.4.6-GCCcore-11.2.0
module list

# Log the loaded modules and environment variables to the same file
{
    module list
    env
    echo $PATH  # Log the PATH variable
} >> $OUT_FILE 2>&1  # Append both stdout and stderr to OUT_FILE

# Execute the MPI program and log the time
{
    time mpirun -n 8 ./bin/regcmMPI test_001.in
} >> $OUT_FILE 2>&1  # Append both stdout and stderr to OUT_FILE
~      
