#!/bin/bash
#SBATCH --job-name=postproc_2002
#SBATCH --output=logs/postproc_all_%j.out
#SBATCH --error=logs/postproc_all_%j.err
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G

START_DATE=$1
END_DATE=$2
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo "Error: Please provide start and end dates (e.g., sbatch slurm/postproc_all.sbatch 2002-01-01 2002-12-31)"
  exit 1
fi

source ~/.bashrc
export POSTPROC_CONFIG=configs/experiments/r3km_2000_2004.yaml

set -euo pipefail

echo "========================================"
echo "Host: $(hostname)"
echo "Date: $(date)"
echo "Config: $POSTPROC_CONFIG"
echo "Processing Period: $START_DATE to $END_DATE"
echo "========================================"

YEAR_START=$(echo $START_DATE | cut -d'-' -f1)
YEAR_END=$(echo $END_DATE | cut -d'-' -f1)

# Étape 1 & 2 : Preprocess et Regrid sous xesmf_env
conda activate xesmf_env
echo "Active environment for preprocess/regrid: $CONDA_DEFAULT_ENV"

for y in $(seq $YEAR_START $YEAR_END); do
    echo "========================================"
    echo "── Year $y : 01_preprocess ──"
    echo "========================================"
    python3 src/commun/01_preprocess.py --year $y --vars pr,tasmax,tasmin

    echo "========================================"
    echo "── Year $y : 02_regrid ──"
    echo "========================================"
    python3 src/commun/02_regrid.py --year $y --vars pr,tasmax,tasmin
done

# Étape 3 : Cartes climatologiques et PDFs sous postproc_env
conda activate postproc_env
echo "Active environment for maps/pdfs: $CONDA_DEFAULT_ENV"

echo "========================================"
echo "── 09_domain_overview ──"
echo "========================================"
python3 src/domain/09_domain_overview.py

echo "========================================"
echo "── 03_climatology_maps ──"
echo "========================================"
python3 src/maps/03_climatology_maps.py --start-date $START_DATE --end-date $END_DATE --vars pr,tasmax,tasmin --allow-partial-period

echo "========================================"
echo "── 04_hourly_precip_pdf ──"
echo "========================================"
python3 src/pdfs/04_hourly_precip_pdf.py --start-date $START_DATE --end-date $END_DATE || echo "Hourly PDF non-bloquant"

echo "========================================"
echo "── 08_daily_station_pdf ──"
echo "========================================"
python3 src/pdfs/08_daily_station_pdf.py --start-date $START_DATE --end-date $END_DATE || echo "Station PDF non-bloquant"

echo "========================================"
echo "Completed at: $(date)"
echo "========================================"
