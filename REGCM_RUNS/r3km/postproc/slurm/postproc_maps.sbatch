#!/bin/bash
#SBATCH --job-name=maps
#SBATCH --output=logs/postproc_maps_%j.out
#SBATCH --error=logs/postproc_maps_%j.err
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

START_DATE=$1
END_DATE=$2
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo "Error: Please provide start and end dates (e.g., sbatch slurm/postproc_maps.sbatch 2000-01-01 2001-08-31)"
  exit 1
fi

source ~/.bashrc
conda activate postproc_env
export POSTPROC_CONFIG=configs/experiments/r3km_2000_2004.yaml

set -euo pipefail

echo "========================================"
echo "Host: $(hostname)"
echo "Date: $(date)"
echo "Active environment: $CONDA_DEFAULT_ENV"
echo "Config: $POSTPROC_CONFIG"
echo "Processing Period: $START_DATE to $END_DATE"
echo "Extra Arguments: ${@:3}"
echo "========================================"

python3 src/maps/03_climatology_maps.py --start-date $START_DATE --end-date $END_DATE --vars pr,tasmax,tasmin ${@:3}
