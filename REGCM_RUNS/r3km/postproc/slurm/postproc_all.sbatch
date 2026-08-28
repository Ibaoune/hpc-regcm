#!/bin/bash
#SBATCH --job-name=postproc
#SBATCH --output=logs/postproc_all_%j.out
#SBATCH --error=logs/postproc_all_%j.err
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G

START_DATE=$1
END_DATE=$2
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo "Error: Please provide start and end dates (e.g., sbatch slurm/postproc_all.sbatch 2000-01-01 2001-08-31)"
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
echo "Processing Period (Maps): $START_DATE to $END_DATE"

echo "========================================"

python3 src/domain/09_domain_overview.py
python3 src/maps/03_climatology_maps.py --start-date $START_DATE --end-date $END_DATE --vars pr,tasmax,tasmin --allow-partial-period
python3 src/pdfs/04_hourly_precip_pdf.py --start-date $START_DATE --end-date $END_DATE
python3 src/pdfs/08_daily_station_pdf.py --start-date $START_DATE --end-date $END_DATE
python3 src/commun/11_generate_readmes.py

echo "========================================"
echo "Completed at: $(date)"
echo "========================================"
