#!/bin/bash
######################
## TOUBKAL    UM6P ##
######################
#SBATCH --job-name=RegCM_Mor_28nds        # Job Name
#SBATCH --output=RegCM_Mor_28nds_%j.log    # standard output
#SBATCH --error=RegCM_Mor_28nds_%j.log    # error output
#SBATCH --nodes=28
#SBATCH --ntasks-per-node=32               # Tasks per node
#SBATCH --time=36:00:00             # Wall clock limit (minutes)
#SBATCH --account=CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU
# Display executed commands
set -x

OUT_FILE="RegCM_Mor_28nds_${SLURM_JOB_ID}.log"

# Load necessary modules
module purge
module load GCC/11.2.0
module load OpenMPI/4.1.1-GCC-11.2.0
module load netCDF/4.8.1-gompi-2021b
module load HDF5/1.12.1-gompi-2021b
module load netCDF-Fortran/4.5.3-gompi-2021b
module load libtool/2.4.6-GCCcore-11.2.0
module list

export UCX_TLS=rc,self,shm
export UCX_IB_RETRY_CNT=16
export UCX_IB_TIMEOUT=20
export UCX_RC_TIMEOUT=20

# Log the loaded modules and environment variables to the same file
{
    module list
    env
    echo $PATH  # Log the PATH variable
} >> $OUT_FILE 2>&1  # Append both stdout and stderr to OUT_FILE

# Execute the MPI program and log the time
{
    time mpirun -n 896 ./bin/regcmMPICLM45 test_0010.in
} >> $OUT_FILE 2>&1  # Append both stdout and stderr to OUT_FILE

# Check if the run was successful
if [ $? -eq 0 ]; then
    echo "Run terminé avec succès. Lancement de l'étape suivante..." >> $OUT_FILE
    mv $OUT_FILE logs/RegCM_Mor_28nds_${SLURM_JOB_ID}_SUCCESS.log
    ./run_chain.py >> logs/RegCM_Mor_28nds_${SLURM_JOB_ID}_SUCCESS.log 2>&1
else
    echo "Erreur pendant le run. Le chaînage est stoppé." >> $OUT_FILE
    mv $OUT_FILE logs/RegCM_Mor_28nds_${SLURM_JOB_ID}_FAILED.log
fi
