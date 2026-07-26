#!/bin/bash
# =====================================================
# Author: M. El Aabaribaoune (@um6p) 
# Description: Build RegCM.
# 
# Usage:
#   ./compile_regcm.sh /absolute_path/to/project /absolute_path/to/arch.env
# 
# Steps:
#   1. Validate input arguments.
#   2. Change to the project directory.
#   3. Run bootstrap.sh to prepare the project.
#   4. Source the environment file.
#   5. Run autoreconf to regenerate configuration files.
#   6. Configure the project.
#   7. Build the project using 'make'.
#   8. Install the project using 'make install'.
# 
# Exit Codes:
#   0  - Success
#   1  - Failure (e.g., invalid arguments, errors during execution)
# =====================================================

set -e  # Exit immediately if a command exits with a non-zero status

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'  # No Color

# Function to log messages with timestamp
log() {
    echo -e "\n$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Function to wait for a specified time
wait_step() {
    sleep 2
}

# Check if the user provided two arguments
if [ "$#" -ne 2 ]; then
    log "Error: Please provide the RegCM directory and the path to the arch.env file."
    log "Example: $0 /path/to/your/RegCMproject /path/to/arch.env"
    exit 1
fi

# Assign the arguments to variables
PROJECT_DIR="$1"
ARCH_ENV="$2"

# Get the full paths
FULL_PROJECT_DIR="$PROJECT_DIR" #$(realpath "$PROJECT_DIR")
FULL_ARCH_ENV="$PROJECT_DIR" #$(realpath "$ARCH_ENV")

# Confirm the paths with the user
log "You provided the following paths:"
log "${GREEN}Project Directory${NC}: $FULL_PROJECT_DIR"
log "${GREEN}Architecture Environment File${NC}: $FULL_ARCH_ENV"
read -p "Are you sure you want to proceed with these paths? (y/n): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    log "Operation canceled by the user."
    exit 0
fi

log "=== Constructing RegCM in $FULL_PROJECT_DIR ==="
wait_step

# Change to the project directory
cd "$PROJECT_DIR" || { log "Error: Failed to change directory to $FULL_PROJECT_DIR. Exiting."; exit 1; }

# Run bootstrap.sh
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 1: Running bootstrap.sh..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step
if [ -f "bootstrap.sh" ]; then
    ./bootstrap.sh || { log "Error: bootstrap.sh failed. Exiting."; exit 1; }
else
    log "Error: bootstrap.sh not found. Exiting."
    exit 1
fi

# Source the environment file
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 2: Sourcing environment from $FULL_ARCH_ENV..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step
if [ -f "$ARCH_ENV" ]; then
    source "$ARCH_ENV" || { log "Error: Failed to source $FULL_ARCH_ENV. Exiting."; exit 1; }
else
    log "Error: Environment file $FULL_ARCH_ENV not found. Exiting."
    exit 1
fi

# Run autoreconf to generate configuration files
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 3: Running autoreconf..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step

autoreconf -f -i || { log "Error: autoreconf failed. Exiting."; exit 1; }

# Configure the project
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 4: Configuring RegCM..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step
./configure  || { log "Error: Configuration failed. Exiting."; exit 1; }

# Build the project
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 5: Building RegCM..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step
make || { log "Error: make failed. Exiting."; exit 1; }

# Install the project
log "++++++++++++++++++++++++++++++++++++++++++++"
log "Step 6: Installing RegCM..."
log "++++++++++++++++++++++++++++++++++++++++++++"
wait_step
make install || { log "Error: Installation failed. Exiting."; exit 1; }

log "=== RegCM construction completed successfully ==="
                                                               
