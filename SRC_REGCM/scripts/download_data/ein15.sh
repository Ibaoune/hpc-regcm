#!/bin/bash
# ---------------------------------------------------------------------------
# Author: M. El Aabaribaoune (@um6p)
# Description:
# This script automates the downloading of REGCM data files for a specified 
# year from the ICTP data site. It checks for required environment variables, 
# allows the user to select which data types to download, and manages 
# directories for organizing the downloaded files. The script will only 
# download files that do not already exist in the target directory.
# ---------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# Define parameters at the beginning of the script
YEAR="1990"
all_types=("air" "hgt" "rhum" "uwnd" "vwnd")
hours=("00" "06" "12" "18")

# Function to check environment variables
check_env_var() {
    local var_name="$1"
    if [ -z "${!var_name}" ]; then
        printf "Error: %s is not set.\n" "$var_name"
        exit 1
    fi
}

# Function to change directory
change_dir() {
    local dir="$1"
    if cd "$dir"; then
        printf "Successfully changed to %s\n" "$dir"
    else
        printf "Failed to change directory to %s. Check if the directory exists.\n" "$dir"
        exit 1
    fi
}

# Function to get user-selected types
get_user_types() {
    echo "Available types: ${all_types[*]}"
    read -p "Do you want to download all types? (y/n): " choice

    if [[ "$choice" == "y" ]]; then
        types=("${all_types[@]}")
    else
        read -p "Enter the types you want to download (separated by spaces): " -a types
        # Validate user input
        for type in "${types[@]}"; do
            if [[ ! " ${all_types[@]} " =~ " ${type} " ]]; then
                printf "Invalid type: %s. Please choose from: %s\n" "$type" "${all_types[*]}"
                exit 1
            fi
        done
    fi
}

# Check required environment variables
check_env_var "REGCM_GLOBEDAT"
check_env_var "ICTP_DATASITE"

printf "Changing to the REGCM_GLOBEDAT directory...\n"
change_dir "$REGCM_GLOBEDAT"

printf "Listing contents of REGCM_GLOBEDAT:\n"
ls

printf "Changing to the EIN15 directory...\n"
change_dir "EIN15"

# Create the YEAR directory
mkdir -p "$YEAR"
printf "Directory %s is ready.\n" "$YEAR"

change_dir "$YEAR"

# Get user-selected types
get_user_types

# Download the files if they do not already exist
for type in "${types[@]}"; do
    for hh in "${hours[@]}"; do
        filename="${type}.${YEAR}.${hh}.nc"

        if [ -f "$filename" ]; then
            printf "%s already exists. Skipping download.\n" "$filename"
        else
            printf "Downloading %s...\n" "$filename"
            if curl -o "$filename" "${ICTP_DATASITE}/EIN15/${YEAR}/$filename"; then
                printf "%s downloaded successfully.\n" "$filename"
            else
                printf "Failed to download %s\n" "$filename"
            fi
        fi
    done
done

printf "Download completed.\n"

