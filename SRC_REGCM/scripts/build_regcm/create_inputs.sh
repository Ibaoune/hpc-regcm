#!/bin/bash

# create_inputs.sh
# A script to generate input files for REGCM by executing terrain, sst, and icbc commands.
#
# Usage: ./create_inputs.sh <input_file>
#
# Ensure that the REGCM_RUN environment variable is set to the appropriate directory.
#
# Author: M. El Aabaribaoune (@um6p)
# Date: 15/10/2024

# Logging function
log() {
  echo "[INFO] $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Check if REGCM_RUN is set
if [ -z "$REGCM_RUN" ]; then
  echo "[ERROR] REGCM_RUN environment variable is not set."
  return 1
fi
log "REGCM_RUN is set to: $REGCM_RUN"

# Check if the input file is provided
if [ "$#" -ne 1 ]; then
  echo "[ERROR] Usage: $0 <input_file>"
  return 1
fi
input_file="$1"
log "Input file specified: $input_file"

# Validate input file
if [ ! -f "$input_file" ]; then
  echo "[ERROR] Input file '$input_file' does not exist or is not a file."
  return 1
fi

# Change directory to REGCM_RUN
cd "$REGCM_RUN" || { echo "[ERROR] Cannot change to directory $REGCM_RUN"; return 1; }
log "Changed directory to REGCM_RUN: $REGCM_RUN"

# Define the paths of the binaries
terrain_bin="./bin/terrain"
sst_bin="./bin/sst"
icbc_bin="./bin/icbc"

# Show the user the commands that will be executed
log "The following commands will be executed:"
log "$terrain_bin $input_file"
log "$sst_bin $input_file"
log "$icbc_bin $input_file"

# Function for user confirmation
confirm() {
  read -p "$1 (yes/no)? " response
  if [[ ! "$response" =~ ^[Yy][Ee]?$ ]]; then
    echo "[INFO] Aborting the execution."
    return 1  # Non-zero exit code for abort
  fi
}

# User confirmations
confirm "The following REGCM_RUN directory '$REGCM_RUN' will be used ! do you confirm ? "

# Execute commands with error handling
execute_command() {
  log "Executing $1 command..."
  if ! "$2" "$input_file"; then
    echo "[ERROR] $1 command failed."
    return 1
  fi
  log "$1 command executed successfully."
}

execute_command "terrain" "$terrain_bin"
execute_command "sst" "$sst_bin"
execute_command "icbc" "$icbc_bin"

log "Inputs created successfully."

