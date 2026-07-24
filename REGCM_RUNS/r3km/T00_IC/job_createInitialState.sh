#!/bin/bash
# ==============================================================================
# Script Name: job_createInitialState.sh
# Description: Slurm job for generating initial conditions and forcings
# Author: M. El Aabaribaoune (@um6p)
# Note: This is an HPC-specific extension developed for managing RegCM simulations
# ==============================================================================
######################
## TOUBKAL    UM6P ##
######################
#SBATCH --job-name=IC_mksfrce
#SBATCH --output=%x_%j.log                 # log SLURM standard
#SBATCH --error=%x_%j.log                  # log SLURM error
#SBATCH --nodes=1
#SBATCH --time=36:00:00
#SBATCH --mem=128G
#SBATCH --account=CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU

set -x

########################################
# Choose which executable to run
########################################

# Uncomment only ONE:
#BIN=terrainCLM45
#BIN=sstCLM45
#BIN=icbcCLM45
BIN=mksurfdataCLM45

INPUT=test_0010.in

########################################
# Output file based on chosen binary
########################################
OUT_FILE="${BIN}_${SLURM_JOB_ID}.log"

echo "Output file = $OUT_FILE"

########################################
# Load environment for RegCM
########################################
source ../../../SRC_REGCM/shells/build_regcm/arch.env
{
    echo "=== MODULE LIST ==="
    module list
} >> "$OUT_FILE" 2>&1
########################################
# Run selected executable
########################################
{
    echo "=== Running $BIN ==="
    time ./bin/$BIN "$INPUT"
} >> "$OUT_FILE" 2>&1

