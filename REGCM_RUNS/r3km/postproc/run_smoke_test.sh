#!/bin/bash
# run_smoke_test.sh
# Executes the Phase 2A-QA plotting diagnostic suite.

export POSTPROC_CONFIG=configs/experiments/r3km_2000_2004.yaml

YEAR=2001
PARTIAL=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --year) YEAR="$2"; shift ;;
        --partial) PARTIAL="--partial" ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "Running Phase 2A Smoke Test for $YEAR $PARTIAL..."
VARS="pr,tasmax,tasmin"

# Run Preprocessing
python3 src/01_preprocess.py --year $YEAR --vars $VARS || exit 1
python3 src/02_regrid.py --year $YEAR --vars $VARS || exit 1

# Plotting Pipeline
python3 src/03_climatology_maps.py --year $YEAR --vars $VARS $PARTIAL || exit 1
python3 src/07_metrics_table.py --year $YEAR --vars $VARS || exit 1
python3 src/08_station_validation.py --year $YEAR $PARTIAL || exit 1
python3 src/09_domain_overview.py --year $YEAR $PARTIAL || exit 1
python3 src/10_precipitation_pdf.py --year $YEAR $PARTIAL || exit 1

echo "Smoke test complete."
