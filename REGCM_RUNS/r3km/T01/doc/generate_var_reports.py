#!/usr/bin/env python3
# ==============================================================================
# Script Name: generate_var_reports.py
# Description: Generates detailed variable reports for each output stream
# Author: M. El Aabaribaoune (@um6p)
# Note: This is an HPC-specific extension developed for managing RegCM simulations
# ==============================================================================
import os
import glob
import subprocess
import re

streams = ['ATM', 'SRF', 'RAD', 'SHF', 'STS', 'SAV']
output_dir = "output"
report_dir = "report_outputs"

# Command prefix to load modules before ncdump
prefix = "module purge && module load GCC/11.2.0 OpenMPI/4.1.1-GCC-11.2.0 netCDF/4.8.1-gompi-2021b && "

def get_timesteps(filepath):
    cmd = prefix + f"ncdump -h {filepath} | grep -i 'time = UNLIMITED'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    m = re.search(r'\((\d+)\s+currently\)', res.stdout)
    if m:
        return int(m.group(1))
    return 1 # Default fallback

def get_variables(filepath):
    cmd = prefix + f"ncdump -h {filepath}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    lines = res.stdout.split('\n')
    in_vars = False
    vars_dict = {}
    current_var = None
    
    for line in lines:
        if line.strip() == "variables:":
            in_vars = True
            continue
        if line.strip() == "// global attributes:":
            break
            
        if in_vars:
            # Match variable declaration: e.g., float t(time, kz, iy, jx) ;
            decl_match = re.match(r'\s*\w+\s+([a-zA-Z0-9_]+)\(.*\)\s*;', line)
            if decl_match:
                current_var = decl_match.group(1)
                vars_dict[current_var] = {'type': line.strip().split()[0], 'long_name': 'N/A', 'units': 'N/A'}
            else:
                # Match attributes: e.g., t:long_name = "temperature" ;
                attr_match = re.match(r'\s*([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)\s*=\s*(.*)\s*;', line)
                if attr_match and current_var == attr_match.group(1):
                    attr_name = attr_match.group(2)
                    attr_val = attr_match.group(3).strip('"')
                    if attr_name in ['long_name', 'units']:
                        vars_dict[current_var][attr_name] = attr_val
                        
    return vars_dict

def analyze_stream(stream):
    files = glob.glob(f"{output_dir}/*_{stream}.*.nc")
    if not files:
        return
        
    print(f"Analyzing stream {stream}...")
    
    # Sort files to get the most recent one as sample
    files.sort()
    sample_file = files[-1]
    
    # Get variables dictionary
    vars_dict = get_variables(sample_file)
    
    # Infer frequency history by grouping files by their approximate size
    # This avoids calling ncdump on 685 files which would be very slow
    cmd = f"stat -c '%s' {output_dir}/*_{stream}.*.nc | awk '{{print int($1/1024/1024/1024) \" Go\"}}' | sort | uniq -c"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    size_dist = res.stdout.strip().split('\n')
    
    freq_history = []
    
    for line in size_dist:
        line = line.strip()
        if not line: continue
        parts = line.split()
        count = int(parts[0])
        size_str = parts[1]
        size_gb = int(size_str)
        
        # Find one file with this approximate size to read its timesteps
        freq_str = "Unknown"
        for f in files:
            size_bytes = os.path.getsize(f)
            if int(size_bytes/1024/1024/1024) == size_gb:
                ts = get_timesteps(f)
                if stream == 'SAV' or ts == 1:
                    freq_str = f"{ts} timestep/file (Monthly / Daily or End of run)"
                elif ts == 24 or ts == 25:
                    freq_str = f"Hourly (1h, {ts} timesteps/file)"
                elif ts == 4 or ts == 5:
                    freq_str = f"6-hourly (6h, {ts} timesteps/file)"
                elif ts == 8 or ts == 9:
                    freq_str = f"3-hourly (3h, {ts} timesteps/file)"
                else:
                    freq_str = f"{ts} timesteps/file"
                break
                
        freq_history.append(f"- {count:4d} files weigh approx {size_gb:2d} GB : Frequency -> {freq_str}")
    
    # Write the report
    report_file = os.path.join(report_dir, f"{stream.lower()}.txt")
    with open(report_file, "w") as f:
        f.write(f"============================================================\n")
        f.write(f" STREAM ANALYSIS REPORT : {stream}\n")
        f.write(f"============================================================\n\n")
        
        f.write(f"1. WRITE FREQUENCY HISTORY OVER THE ENTIRE SIMULATION :\n")
        f.write(f"------------------------------------------------------------------\n")
        f.write(f"Total files found : {len(files)}\n")
        for h in freq_history:
            f.write(f"{h}\n")
            
        f.write(f"\n2. VARIABLES CONTAINED IN THIS STREAM (from the last file) :\n")
        f.write(f"-----------------------------------------------------------------\n")
        f.write(f"{'Variable':<15} | {'Unit':<20} | {'Description (long_name)'}\n")
        f.write("-" * 90 + "\n")
        
        coords = ['lon', 'lat', 'time', 'x', 'y', 'iy', 'jx', 'kz', 'crs', 'time_bnds', 'lev']
        for vname, vinfo in vars_dict.items():
            # Skip pure coordinate/grid variables to only show physical variables
            if vname in coords:
                continue
            f.write(f"{vname:<15} | {vinfo['units']:<20} | {vinfo['long_name']}\n")

for stream in streams:
    analyze_stream(stream)
    
print(f"\\nReports generated successfully in {report_dir}/ directory")
