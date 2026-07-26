#!/bin/bash
# Author: M. El Aabaribaoune (@um6p)
# Description:
# This script documents how the customized RegCM-Toubkal version of the source code
# is compiled on the Toubkal HPC cluster.

# Stop on any error
set -e

# Load the environment modules specifically needed for Toubkal
echo "Loading environment modules..."
source arch_RegCM4.5_Tbkl.env

echo "Entering RegCM-4.5.0 directory..."
cd RegCM-4.5.0/

echo "Configuring RegCM for compilation..."
# Adjust configuration flags here if necessary based on your usual setup
./configure

echo "Compiling RegCM..."
# Use multiple cores for faster compilation
make -j 8

echo "Compilation completed successfully!"
