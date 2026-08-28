#!/bin/bash
#SBATCH --job-name=domain
#SBATCH --output=logs/postproc_domain_%j.out
#SBATCH --error=logs/postproc_domain_%j.err
#SBATCH --time=01:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

source ~/.bashrc
conda activate postproc_env
export POSTPROC_CONFIG=configs/experiments/r3km_2000_2004.yaml

set -euo pipefail

echo "========================================"
echo "Host: $(hostname)"
echo "Date: $(date)"
echo "Active environment: $CONDA_DEFAULT_ENV"
echo "Config: $POSTPROC_CONFIG"
echo "========================================"

python3 src/domain/09_domain_overview.py
