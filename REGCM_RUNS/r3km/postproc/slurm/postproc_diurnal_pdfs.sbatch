#!/bin/bash
#SBATCH --job-name=pp_diur_pdf
#SBATCH --output=logs/postproc_diurnal_pdfs_%j.out
#SBATCH --error=logs/postproc_diurnal_pdfs_%j.err
#SBATCH --time=08:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G

# Usage: sbatch slurm/postproc_diurnal_pdfs.sbatch 2000-01-01 2002-12-31
START_DATE=$1
END_DATE=$2
if [ -z "$START_DATE" ] || [ -z "$END_DATE" ]; then
  echo "Usage: sbatch slurm/postproc_diurnal_pdfs.sbatch YYYY-MM-DD YYYY-MM-DD"; exit 1
fi

source ~/.bashrc
conda activate postproc_env
export POSTPROC_CONFIG=configs/experiments/r3km_2000_2004.yaml
echo "Host: $(hostname) | Start: $(date) | Period: $START_DATE -> $END_DATE"

echo "── 05_diurnal_cycle ──"
python3 -u src/diurnal/05_diurnal_cycle.py --start-date $START_DATE --end-date $END_DATE --vars pr,tas || echo "[FAIL] diurnal"

echo "── 04_hourly_precip_pdf ──"
python3 -u src/pdfs/04_hourly_precip_pdf.py --start-date $START_DATE --end-date $END_DATE || echo "[FAIL] hourly pdf"

echo "── 08_daily_station_pdf ──"
python3 -u src/pdfs/08_daily_station_pdf.py --start-date $START_DATE --end-date $END_DATE || echo "[FAIL] station pdf"

echo "Completed: $(date)"
