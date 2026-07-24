#!/usr/bin/env python3
# ==============================================================================
# Script Name: generate_forcing_report.py
# Description: Generates report for forcing data and initial conditions
# Author: M. El Aabaribaoune (@um6p)
# Note: This is an HPC-specific extension developed for managing RegCM simulations
# ==============================================================================
import os
import subprocess
import glob
import re

report_file = "../reports/report_forcing_IC.md"
ic_dir = "../../T00_IC/input"
prefix = "module purge && module load GCC/11.2.0 OpenMPI/4.1.1-GCC-11.2.0 netCDF/4.8.1-gompi-2021b && "

def get_ncdump_h(filepath):
    cmd = prefix + f"ncdump -h {filepath}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout

def parse_global_attributes(ncdump_output):
    attrs = {}
    in_global = False
    for line in ncdump_output.split('\n'):
        if line.strip() == "// global attributes:":
            in_global = True
            continue
        if in_global:
            m = re.match(r'\s*:([a-zA-Z0-9_]+)\s*=\s*(.*)\s*;', line)
            if m:
                attrs[m.group(1)] = m.group(2).strip('"')
    return attrs

def parse_variables(ncdump_output):
    vars_list = []
    in_vars = False
    for line in ncdump_output.split('\n'):
        if line.strip() == "variables:":
            in_vars = True
            continue
        if line.strip() == "// global attributes:":
            break
        if in_vars:
            m = re.match(r'\s*\w+\s+([a-zA-Z0-9_]+)\(.*\)\s*;', line)
            if m:
                vars_list.append(m.group(1))
    return vars_list

def main():
    icbc_files = sorted(glob.glob(f"{ic_dir}/*_ICBC.*.nc"))
    sst_files = sorted(glob.glob(f"{ic_dir}/*_SST.nc"))
    
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w") as f:
        f.write("# DOCUMENTATION OF FORCINGS AND INITIAL CONDITIONS (IC/BC)\n\n")
        
        f.write("## 1. BOUNDARY AND INITIAL CONDITIONS (ICBC)\n")
        if not icbc_files:
            f.write("No ICBC file found.\n")
        else:
            first_icbc = icbc_files[0]
            f.write(f"- **Analyzed file:** {os.path.basename(first_icbc)}\n")
            f.write(f"- **Total ICBC files found:** {len(icbc_files)}\n\n")
            
            ncdump_out = get_ncdump_h(first_icbc)
            attrs = parse_global_attributes(ncdump_out)
            
            f.write("### Global Metadata\n\n")
            for k, v in attrs.items():
                f.write(f"- **{k}:** {v}\n")
                
            vars_list = parse_variables(ncdump_out)
            f.write("\n### Included Variables\n\n")
            f.write(f"`{', '.join([v for v in vars_list if v not in ['lon', 'lat', 'time', 'x', 'y', 'kz', 'crs']])}`\n\n")
            
            f.write(f"**Average size per monthly file:** ~95 GB (based on inventory)\n\n")
            
        f.write("## 2. OCEANIC FORCING (SST)\n")
        if not sst_files:
            f.write("No SST file found.\n")
        else:
            sst_file = sst_files[0]
            f.write(f"- **Analyzed file:** {os.path.basename(sst_file)}\n\n")
            
            ncdump_out = get_ncdump_h(sst_file)
            attrs = parse_global_attributes(ncdump_out)
            
            f.write("### Global Metadata\n\n")
            for k, v in attrs.items():
                f.write(f"- **{k}:** {v}\n")
                
            vars_list = parse_variables(ncdump_out)
            f.write("\n### Included Variables\n\n")
            f.write(f"`{', '.join([v for v in vars_list if v not in ['lon', 'lat', 'time', 'x', 'y', 'crs']])}`\n\n")
            
        f.write("## 3. LAND SURFACE (LANDUSE / TEXTURE)\n")
        f.write("Binary/text files used:\n")
        f.write("- `test_001_LANDUSE`\n")
        f.write("- `test_001_TEXTURE`\n\n")
        
        f.write("## CONFIGURATION SUMMARY (from test_0010.in)\n")
        f.write("- **ssttyp:** 'ERA5'\n")
        f.write("- **dattyp:** 'ERA5'\n")
        f.write("- **Global start date (gdate1):** 1999-01-01\n")
        f.write("- **Global end date (gdate2):** Varies per period\n")
        f.write("- **Boundary conditions frequency (ibdyfrq):** 6 hours\n")

    print(f"Report generated successfully in {os.path.abspath(report_file)}")

if __name__ == "__main__":
    main()
