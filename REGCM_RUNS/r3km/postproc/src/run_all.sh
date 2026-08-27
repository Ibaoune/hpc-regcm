#!/bin/bash
set -e

CONFIG_FILE=$1

if [ -z "$CONFIG_FILE" ]; then
    echo "Usage: bash src/run_all.sh <path_to_config.yaml>"
    exit 1
fi

export POSTPROC_CONFIG=$(realpath "$CONFIG_FILE")

# Helper to check if module is enabled in YAML
check_module() {
    python3 -c "
import yaml
with open('$POSTPROC_CONFIG', 'r') as f:
    cfg = yaml.safe_load(f)
print('true' if cfg.get('modules', {}).get('$1', False) else 'false')
"
}

echo "=========================================================="
echo " Starting RegCM Post-Processing Pipeline"
echo " Config: $POSTPROC_CONFIG"
echo "=========================================================="

if [ "$(check_module 'do_monitor')" = "true" ]; then
    python3 src/00_monitor.py
fi

if [ "$(check_module 'do_preprocess')" = "true" ]; then
    python3 src/01_preprocess.py --year 2000
fi

if [ "$(check_module 'do_regrid')" = "true" ]; then
    python3 src/02_regrid.py --year 2000
fi

# The other modules are not strictly required to be completely refactored in Phase 1B (only visual configs), 
# but they should run without error if they were already working and we just updated config_parser.py
if [ "$(check_module 'do_climatology')" = "true" ] && [ -f "src/03_climatology_maps.py" ]; then
    python3 src/03_climatology_maps.py
fi

if [ "$(check_module 'do_bias_maps')" = "true" ] && [ -f "src/04_bias_maps.py" ]; then
    python3 src/04_bias_maps.py
fi

if [ "$(check_module 'do_timeseries')" = "true" ] && [ -f "src/05_seasonal_cycle.py" ]; then
    python3 src/05_seasonal_cycle.py
fi

if [ "$(check_module 'do_taylor')" = "true" ] && [ -f "src/06_taylor_diagram.py" ]; then
    python3 src/06_taylor_diagram.py
fi

if [ "$(check_module 'do_metrics_table')" = "true" ] && [ -f "src/07_metrics_table.py" ]; then
    python3 src/07_metrics_table.py
fi

echo "=========================================================="
echo " Pipeline Finished Successfully."
echo "=========================================================="
