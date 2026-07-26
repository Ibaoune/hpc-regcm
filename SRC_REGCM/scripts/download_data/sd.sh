#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Author: M. El Aabaribaoune (@um6p)
# Description:
# This script checks for necessary environment variables, navigates to the 
# REGCM_GLOBEDAT directory, and downloads specified surface datasets from the 
# ICTP data site. It ensures that each dataset is only downloaded if it does 
# not already exist in the directory. An optional lake dataset can also be downloaded.
# ---------------------------------------------------------------------------

set -e  # Exit immediately if a command exits with a non-zero status

# Define parameters at the beginning of the script
SURFACE_DIR="SURFACE"

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

# Function to download a dataset
download_dataset() {
    local dataset="$1"
    echo "Downloading $dataset..."
    if curl -o "$dataset" "${ICTP_DATASITE}/SURFACE/$dataset"; then
        echo "$dataset downloaded successfully."
    else
        echo "Failed to download $dataset"
    fi
}

# Check required environment variables
check_env_var "REGCM_GLOBEDAT"
check_env_var "ICTP_DATASITE"

# Navigate to the REGCM_GLOBEDAT directory
echo "Changing to the REGCM_GLOBEDAT directory..."
change_dir "$REGCM_GLOBEDAT"

# Navigate to the SURFACE directory
echo "Changing to the $SURFACE_DIR directory..."
change_dir "$SURFACE_DIR"

# Download the primary datasets
datasets=(
    "GTOPO_DEM_30s.nc"
    "GLCC_BATS_30s.nc"
    "GLZB_SOIL_30s.nc"
)

for dataset in "${datasets[@]}"; do
    if [ -f "$dataset" ]; then
        echo "$dataset already exists. Skipping download."
    else
        download_dataset "$dataset"
    fi
done

# Optional: Download the Lake dataset
lake_dataset="ETOPO_BTM_30s.nc"
if [ -f "$lake_dataset" ]; then
    echo "$lake_dataset already exists. Skipping download."
else
    echo "Downloading optional Lake dataset $lake_dataset..."
    curl -o "$lake_dataset" "${ICTP_DATASITE}/SURFACE/$lake_dataset" || {
        echo "Failed to download $lake_dataset"
    }
fi

echo "Download completed."

