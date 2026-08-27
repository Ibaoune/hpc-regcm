#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
import sys, os, glob
import netCDF4 as nc
import pandas as pd
from pathlib import Path
import cftime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.config_parser as cp

MONITOR_DIR = cp.RESULTS_DIR / "monitoring"
MONITOR_DIR.mkdir(parents=True, exist_ok=True)

def analyze_stream(stream, year):
    files = sorted(glob.glob(f"{cp.OUTPUT_DIR}/*_{stream}.{year}*.nc"))
    if not files: return None
    
    first_file = files[0]
    last_file = files[-1]
    
    try:
        ds_first = nc.Dataset(first_file)
        t_var = ds_first.variables['time']
        if len(t_var) == 0:
            raise ValueError("Time variable is empty in first file")
            
        if len(t_var) > 1:
            timestep = t_var[1] - t_var[0]
        else:
            timestep = "N/A"
            
        ds_last = nc.Dataset(last_file)
        t_last_var = ds_last.variables['time']
        if len(t_last_var) == 0:
            raise ValueError("Time variable is empty in last file")
        
        dates_first = cftime.num2date(t_var[:], units=t_var.units, calendar=getattr(t_var, 'calendar', 'standard'))
        dates_last = cftime.num2date(t_last_var[:], units=t_last_var.units, calendar=getattr(t_last_var, 'calendar', 'standard'))
        
        is_complete = False
        if dates_last[-1].month == 12 and dates_last[-1].day >= 31:
            is_complete = True
            
        return {
            "stream": stream,
            "year": year,
            "first_file": os.path.basename(first_file),
            "last_file": os.path.basename(last_file),
            "records_per_file": len(t_var),
            "internal_timestep": timestep,
            "time_units": t_var.units,
            "file_count": len(files),
            "is_complete": is_complete,
            "first_date": str(dates_first[0]),
            "last_date": str(dates_last[-1])
        }
    except Exception as e:
        print(f"Error reading {first_file} or {last_file}: {e}")
        return None

def main():
    print(f"\\n{'='*60}")
    print(f"  REGCM r3km STATUS MONITORING")
    print(f"{'='*60}")
    
    # We will check from SPINUP_YEAR to the end of evaluation 
    # For now, let's check up to 2004
    years = list(range(cp.SPINUP_YEAR, 2005))
    streams = ['STS', 'SRF', 'ATM', 'RAD', 'SHF']
    
    status_list = []
    
    for y in years:
        y_status = "NOT STARTED"
        period_type = "SPIN-UP" if y == cp.SPINUP_YEAR else "EVALUATION"
        last_date_str = ""
        
        stream_results = []
        for s in streams:
            res = analyze_stream(s, y)
            if res:
                stream_results.append(res)
        
        if stream_results:
            is_complete = all(r['is_complete'] for r in stream_results)
            if is_complete:
                y_status = "COMPLETE"
            else:
                y_status = "RUNNING"
                last_date_str = f"last timestep: {stream_results[0]['last_date']}"
        
        print(f"{y}   {period_type:<10}  {y_status:<11} {last_date_str}")
        
        for r in stream_results:
            print(f"    {r['stream']:<4} | Files: {r['file_count']:<4} | Rec/file: {r['records_per_file']:<4} | dt: {r['internal_timestep']:<4} | First: {r['first_date']} | Last: {r['last_date']}")
            status_list.append(r)
            
    if not status_list:
        print("No files found.")
        return
        
    df = pd.DataFrame(status_list)
    csv_path = MONITOR_DIR / "status.csv"
    md_path = MONITOR_DIR / "status.md"
    
    df.to_csv(csv_path, index=False)
    md_str = "# RegCM Stream Frequencies and Status\\n\\n"
    for idx, row in df.iterrows():
        md_str += f"### {row['stream']} ({row['year']})\\n"
        for col in df.columns:
            md_str += f"- **{col}**: {row[col]}\\n"
        md_str += f"- **latest_valid_timestamp**: {row['last_timestep']}\\n"
        md_str += "\\n"
        
    with open(md_path, 'w') as f:
        f.write(md_str)
        
    print(f"\\n✔ Saved to {csv_path} and {md_path}\\n")

if __name__ == "__main__":
    main()
