#!/bin/bash
# ---------------------------------------------------------------------------
# Author: M. El Aabaribaoune (@um6p)
# Description:
# This script checks for the necessary environment variables and navigates to 
# the REGCM_GLOBEDAT directory to download specified CLM datasets from the 
# ICTP data site. It ensures that each dataset is only downloaded if it does 
# not already exist in the directory.
# ---------------------------------------------------------------------------

# Define parameters at the beginning of the script
CLM_DIR="CLM"

# Function to check environment variables
check_env_var() {
    local var_name="$1"
    if [ -z "${!var_name}" ]; then
        echo "Error: $var_name is not set."
        exit 1
    fi
}

# Function to change directory
change_dir() {
    local dir="$1"
    if cd "$dir"; then
        echo "Successfully changed to $dir"
    else
        echo "Failed to change directory to $dir. Check if the directory exists."
        exit 1
    fi
}

# Check required environment variables
check_env_var "REGCM_GLOBEDAT"
check_env_var "ICTP_DATASITE"

# Navigate to the REGCM_GLOBEDAT directory
echo "Changing to the REGCM_GLOBEDAT directory..."
change_dir "$REGCM_GLOBEDAT"

# Navigate to the CLM directory
echo "Changing to the $CLM_DIR directory..."
change_dir "$CLM_DIR"

# List of datasets to download
datasets=(
    "mksrf_fmax.nc"
    "mksrf_glacier.nc"
    "mksrf_lai.nc"
    "mksrf_lanwat.nc"
    "mksrf_navyoro_20min.nc"
    "mksrf_pft.nc"
    "mksrf_soicol_clm2.nc"
    "mksrf_soitex.10level.nc"
    "mksrf_urban.nc"
    "pft-physiology.c070207"
    "pft-physiology.c070207.readme"
    "rdirc.05.061026"
)

# Download each dataset
for dataset in "${datasets[@]}"; do
    if [ -f "$dataset" ]; then
        echo "$dataset already exists. Skipping download."
    else
        echo "Downloading $dataset..."
        curl -o "$dataset" "${ICTP_DATASITE}/CLM/$dataset" || {
            echo "Failed to download $dataset"
            continue
        }
        echo "$dataset downloaded successfully."
    fi
done

echo "Download completed."

