#!/bin/bash
# Author : M. El Aabaribaoune (@um6p)


# Script to extract a specified variable from multiple "test_001_SRF.*.nc" files and merge them
#
# Usage:
#   ./extract_and_merge.sh <variable_name>
#
# What it does:
# 1. Checks that a variable name is provided as an argument.
# 2. Loads the CDO (Climate Data Operators) module.
# 3. Extracts the specified variable from all NetCDF files matching the pattern "test_001_SRF.*.nc".
# 4. Saves each extracted variable as a separate file prefixed with the variable name.
# 5. Merges all extracted files along the time dimension into a single NetCDF file named "merged_<variable_name>.nc".
# 6. Removes the intermediate extracted files.
#
# Requirements:
# - CDO installed and accessible via module system.
# - Input files named with pattern "test_001_SRF.*.nc".
#
# Example:
#   ./extract_and_merge.sh pr



# Check if a variable name is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <variable_name>"
    exit 1
fi

VAR_NAME="$1"

# Load CDO
module load CDO/2.0.5-gompi-2021b

# Extract specified variable from each NetCDF file
echo "Extracting '$VAR_NAME' from NetCDF files..."
for file in test_001_SRF.*.nc; do
    if [[ -e "$file" ]]; then
        output_file="${VAR_NAME}_${file}"
        cdo selname,"$VAR_NAME" "$file" "$output_file"
        echo "Extracted '$VAR_NAME' from $file to $output_file"
    else
        echo "No files matching pattern found: test_001_SRF.*.nc"
        exit 1
    fi
done

# Merge all extracted files into one
echo "Merging extracted files into merged_${VAR_NAME}.nc..."
cdo mergetime "${VAR_NAME}_test_001_SRF.*.nc" "merged_${VAR_NAME}.nc"
if [[ $? -eq 0 ]]; then
    echo "Successfully merged files into merged_${VAR_NAME}.nc"
else
    echo "Error merging files."
fi

# Clean up intermediate files
rm "${VAR_NAME}_"*

