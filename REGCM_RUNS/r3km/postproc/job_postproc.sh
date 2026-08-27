#!/bin/bash
# ==============================================================================
# Script Name: job_postproc.sh
# Description: Slurm job submission script for r3km RegCM postprocessing
#              Runs the full postprocessing pipeline (steps 00–07):
#              precipitation, tasmax, tasmin vs MSWEP / CPC — year 2000
# Author: M. El Aabaribaoune (@um6p)
# Usage: sbatch postproc/job_postproc.sh
#        (must be submitted from r3km/ root directory)
# ==============================================================================
######################
##  TOUBKAL  UM6P  ##
######################
#SBATCH --job-name=r3km_postproc
#SBATCH --output=postproc/logs/postproc_%j.log
#SBATCH --error=postproc/logs/postproc_%j.log
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=04:00:00
#SBATCH --account=CLIMAT-UM6P-ST-IWRI-7KSIFKVWKUY-DEFAULT-CPU

set -euo pipefail
set -x

# ─── Environment ─────────────────────────────────────────────────────────────
module purge
module load Anaconda3/2020.11

PYTHON=/srv/software/easybuild/software/Anaconda3/2020.11/bin/python3
POSTPROC_DIR="$(pwd)/postproc"
LOG_DIR="${POSTPROC_DIR}/logs"
mkdir -p "${LOG_DIR}"

LOG="${LOG_DIR}/postproc_${SLURM_JOB_ID}.log"

echo "======================================================" | tee -a "${LOG}"
echo "  r3km postprocessing pipeline" | tee -a "${LOG}"
echo "  Job ID   : ${SLURM_JOB_ID}" | tee -a "${LOG}"
echo "  Node     : $(hostname)" | tee -a "${LOG}"
echo "  Python   : $($PYTHON --version 2>&1)" | tee -a "${LOG}"
echo "  Start    : $(date)" | tee -a "${LOG}"
echo "  Workdir  : $(pwd)" | tee -a "${LOG}"
echo "======================================================" | tee -a "${LOG}"

# ─── Pipeline ────────────────────────────────────────────────────────────────
cd "${POSTPROC_DIR}"

# Lancement du script maître YAML-driven
bash src/run_all.sh configs/default_eval.yaml 2>&1 | tee -a "${LOG}"
rc=${PIPESTATUS[0]}

if [ ${rc} -ne 0 ]; then
    echo "   FAILED (exit ${rc}) — aborting pipeline." | tee -a "${LOG}"
    mv "${LOG}" "${LOG_DIR}/postproc_${SLURM_JOB_ID}_FAILED.log"
    exit ${rc}
fi

# ─── Summary ─────────────────────────────────────────────────────────────────
echo "" | tee -a "${LOG}"
echo "======================================================" | tee -a "${LOG}"
echo "  ✔  Pipeline complete" | tee -a "${LOG}"
echo "  End: $(date)" | tee -a "${LOG}"
echo "  Results:" | tee -a "${LOG}"
echo "    ${POSTPROC_DIR}/results/maps/" | tee -a "${LOG}"
echo "    ${POSTPROC_DIR}/results/timeseries/" | tee -a "${LOG}"
echo "    ${POSTPROC_DIR}/results/taylor/" | tee -a "${LOG}"
echo "    ${POSTPROC_DIR}/results/tables/" | tee -a "${LOG}"
echo "======================================================" | tee -a "${LOG}"

mv "${LOG}" "${LOG_DIR}/postproc_${SLURM_JOB_ID}_SUCCESS.log"
