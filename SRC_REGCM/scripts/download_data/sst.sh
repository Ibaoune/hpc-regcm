#!/bin/bash
# ---------------------------------------------------------------------------
# Author: M. El Aabaribaoune (@um6p)
# Description:
# This script navigates to the specified directory for REGCM data and downloads
# weekly mean sea surface temperature (SST) files from the NOAA Climate Data 
# Center (CDC) if they do not already exist. The script checks for the presence 
# of required directories and files, and provides feedback throughout the process.
# ---------------------------------------------------------------------------

# Navigate to the specified directory
echo "Navigating to directory: $REGCM_GLOBEDAT"
cd "$REGCM_GLOBEDAT" || { echo "Directory not found: $REGCM_GLOBEDAT"; exit 1; }

echo "Navigating to SST directory"
cd SST || { echo "Directory not found: SST"; exit 1; }

# Define the CDC site variable
CDCSITE="ftp.cdc.noaa.gov/pub/Datasets/noaa.oisst.v2"

# Files to download
files=(
    "sst.wkmean.1981-1989.nc"
    "sst.wkmean.1990-present.nc"
)

# Download the SST files if they do not exist
for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo "$file already exists. Skipping download."
    else
        echo "Downloading $file..."
        curl -o "$file" "ftp://$CDCSITE/$file" || { echo "Failed to download $file"; exit 1; }
        echo "$file downloaded successfully."
    fi
done

