#!/bin/bash
# ==============================================================================
# Script Name: compile_regcm.sh
# Author: M. El Aabaribaoune (@um6p)
# Description:
#   Compiles the customized RegCM-Toubkal source code on the Toubkal HPC cluster
#   with CLM45 land surface model support enabled.
#
# Usage: Run from the SRC_REGCM/ directory:
#   cd SRC_REGCM/
#   ./compile_regcm.sh
#
# NOTE: -j 1 is required (not -j 8) to respect Fortran module dependency order.
#   Parallel compilation causes "Cannot open module file" errors.
# ==============================================================================

# Stop on any error
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin"
SRC_DIR="$SCRIPT_DIR/RegCM-4.5.0"

# Load the environment modules specifically needed for Toubkal
echo "Loading environment modules..."
source "$SCRIPT_DIR/arch_RegCM4.5_Tbkl.env"

# Run bootstrap if configure does not exist yet
cd "$SRC_DIR"
if [ ! -f configure ]; then
    echo "Running bootstrap.sh to generate configure script..."
    ./bootstrap.sh
fi

echo "Configuring RegCM for compilation (with CLM45 support)..."
./configure --enable-clm45

echo "Compiling RegCM (sequential build to respect Fortran module order)..."
make -j 1

echo "Copying regcmMPICLM45 binary to $BIN_DIR ..."
mkdir -p "$BIN_DIR"
cp Main/regcm "$BIN_DIR/regcmMPICLM45"

echo ""
echo "=== Compilation completed successfully! ==="
echo "Binary available at: $BIN_DIR/regcmMPICLM45"
