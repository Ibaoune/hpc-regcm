#!/bin/bash
# ---------------------------------------------------------------------------
# Author: M. El Abaribaoune (@um6p)
# Description:
# This script sets the necessary environment variables for the RegCM (Regional 
# Climate Model) framework. It prompts the user for the REGCM_ROOT and 
# REGCM_RUN directories and checks the existence of the specified directories, 
# providing warnings if any are missing.
# ---------------------------------------------------------------------------

# Define color codes
RED="\e[31m"
GREEN="\e[32m"
RESET="\e[0m"

# Prompt for REGCM_ROOT directory
read -p "Enter the path for REGCM_ROOT (the directory that conatins the bin): " input_regcm_root

# Set REGCM_ROOT to user input
export REGCM_ROOT="$input_regcm_root"

# Prompt for REGCM_RUN directory
read -p "Enter the path for REGCM_RUN (contains 'input' dir): " input_regcm_run

# Set REGCM_RUN to user input
export REGCM_RUN="$input_regcm_run"

# Define other variables
export ICTP_DATASITE="http://clima-dods.ictp.it/regcm4"
export REGCM_GLOBEDAT="/home/$USER/lustre/climat-um6p-st-iwri-7ksifkvwkuy/shared/data/REGCM_GLOBEDAT"
# Function to check if a directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        echo -e "${RED}Warning: Directory '$1' does not exist.${RESET}"
    else
        echo "Directory '$1' exists."
    fi
}

# Check the directories
check_directory "$REGCM_ROOT"
check_directory "$REGCM_GLOBEDAT"
check_directory "$REGCM_RUN"

# Print success message
echo "Environment variables for RegCM have been set."

# Print all set variables with variable names in green
echo -e "The following environment variables have been set:"
echo -e "${GREEN}REGCM_ROOT:${RESET} $REGCM_ROOT"
echo -e "${GREEN}ICTP_DATASITE:${RESET} $ICTP_DATASITE"
echo -e "${GREEN}REGCM_GLOBEDAT:${RESET} $REGCM_GLOBEDAT"
echo -e "${GREEN}REGCM_RUN:${RESET} $REGCM_RUN"

