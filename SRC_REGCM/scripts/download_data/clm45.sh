#!/bin/bash
# ---------------------------------------------------------------------------
# Author: M. El Aabariboune (@um6p)
# Description:
# This script checks for necessary environment variables, navigates to the 
# REGCM_GLOBEDAT directory, and creates specified subdirectories for 
# CLM45 data. It then downloads all available .nc files from each 
# subdirectory on the ICTP data site if they do not already exist.
# ---------------------------------------------------------------------------

# Define parameters at the beginning of the script
CLM45_DIR="CLM45"
SUBDIRS=("megan" "pftdata" "snicardata" "surface")

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

# Navigate to the CLM45 directory
echo "Changing to the $CLM45_DIR directory..."
change_dir "$CLM45_DIR"

# Create the specified subdirectories if they don't exist
for dir in "${SUBDIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Directory $dir already exists. Skipping creation."
    else
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

# Download .nc files from each subdirectory
for dir in "${SUBDIRS[@]}"; do
    echo "Changing to the $dir directory..."
    change_dir "$dir"

    # Get the list of .nc files from the server
    echo "Checking for .nc files in ${ICTP_DATASITE}/CLM45/$dir/"
    wget -q -O - "${ICTP_DATASITE}/CLM45/$dir/" | grep -oP 'href="\K[^"]*\.nc' | while read -r file; do
        if [ -f "$file" ]; then
            echo "$file already exists. Skipping download."
        else
            echo "Downloading $file..."
            wget "${ICTP_DATASITE}/CLM45/$dir/$file" || {
                echo "Failed to download $file"
            }
        fi
    done

    # Go back to the CLM45 directory for the next iteration
    cd ..
done

echo "Download completed."

