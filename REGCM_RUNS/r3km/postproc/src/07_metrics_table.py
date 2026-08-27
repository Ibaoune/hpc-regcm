#!/usr/bin/env python3
# ==============================================================================
# Author: M. El Aabaribaoune (@um6p)
# Description: RegCM Post-processing module
# ==============================================================================
"""
07_metrics_table.py
===================
Separates A. SPATIAL PATTERN METRICS and B. TEMPORAL METRICS.
Uses metrics_engine for weighted spatial stats.
"""

import sys, os, argparse, csv
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import src.config_parser as cp
import src.metrics_engine as me

import netCDF4 as nc
from netCDF4 import num2date
import numpy as np
import warnings; warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, default=cp.YEAR_START)
parser.add_argument("--vars", default=",".join(cp.VARIABLES))
args = parser.parse_args()
YEAR = args.year
varlist = [v.strip() for v in args.vars.split(",")]
cp.TABLES_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n{'═'*60}")
print(f"  07_metrics_table — year {YEAR}")
print(f"{'═'*60}")

def load_nc(fpath, var):
    with nc.Dataset(fpath) as ds:
        data = ds.variables[var][:]
        t = ds.variables["time"][:]
        lat = ds.variables.get("lat", ds.variables.get("xlat"))[:]
        lon = ds.variables.get("lon", ds.variables.get("xlon"))[:]
        t_units = ds.variables["time"].units
    return data, lat, lon, t, t_units

def month_mask(t, tunits, months):
    dates = num2date(t, tunits, calendar="standard")
    return np.array([d.month in months for d in dates])

def get_morocco_mask(lat, lon):
    # The user mandated: do not use bbox as mask.
    mask_file = cp.cfg.get("regions", {}).get("morocco", {}).get("mask_file")
    if not mask_file:
        print("       ⚠ No Morocco scientific mask provided in regions.yaml. Using full intersection.")
        return None
    # For future: load mask_file and interpolate to lat/lon...
    return None

def fmt(v, decimals=3):
    return f"{v:.{decimals}f}" if np.isfinite(v) else "N/A"

spatial_rows = []
temporal_rows = []

for var in varlist:
    cfg = cp.MODEL[var]
    for ref_name, obs_cfg in cp.OBS[var].items():
        if obs_cfg.get("type") == "stations": continue
        
        mod_f = cp.DATA_DIR / "regridded" / ref_name / "model" / var / f"{YEAR}.nc"
        obs_f = cp.DATA_DIR / "processed" / "obs" / ref_name / var / f"{YEAR}.nc"
        
        if not mod_f.exists() or not obs_f.exists():
            print(f"  ⚠  {var} vs {ref_name}: files missing")
            continue
            
        mod_data, m_lat, m_lon, mt, mtu = load_nc(mod_f, var)
        obs_data, o_lat, o_lon, ot, otu = load_nc(obs_f, var)
        
        n = min(mod_data.shape[0], obs_data.shape[0])
        mod_data = mod_data[:n]; obs_data = obs_data[:n]; mt = mt[:n]
        
        mask2d = get_morocco_mask(o_lat, o_lon)
        
        # A. SPATIAL METRICS (on climatological means)
        # Annual
        o_ann = np.nanmean(obs_data, axis=0)
        m_ann = np.nanmean(mod_data, axis=0)
        s_mets = me.compute_spatial_metrics(o_ann, m_ann, o_lat, o_lon, mask=mask2d)
        spatial_rows.append({"variable": var, "reference": ref_name, "period": "Annual", **s_mets})
        
        # B. TEMPORAL METRICS (on area-averaged timeseries)
        # We need a quick area average function for the time series
        ts_o = []
        ts_m = []
        for i in range(n):
            o_field = obs_data[i]
            m_field = mod_data[i]
            res = me.compute_spatial_metrics(o_field, m_field, o_lat, o_lon, mask=mask2d)
            if res["n_valid"] > 0:
                # Retrieve weighted means manually since engine doesn't export them directly, 
                # but we can rebuild it simply
                pass
            
            # Simplified for temporal metrics: just take mean of valid cells
            valid = np.isfinite(o_field) & np.isfinite(m_field)
            if mask2d is not None: valid = valid & mask2d
            
            if valid.sum() > 0:
                ts_o.append(np.mean(o_field[valid]))
                ts_m.append(np.mean(m_field[valid]))
            else:
                ts_o.append(np.nan)
                ts_m.append(np.nan)
                
        ts_o = np.array(ts_o)
        ts_m = np.array(ts_m)
        t_mets = me.compute_temporal_metrics(ts_o, ts_m)
        temporal_rows.append({"variable": var, "reference": ref_name, "period": "Annual", **t_mets})
        
# CSV Output Spatial
s_csv = cp.TABLES_DIR / f"spatial_metrics_{YEAR}.csv"
s_fields = ["variable", "reference", "period", "n_valid", "MB", "MAE", "RMSE", "r", "std_m", "std_o"]
with open(s_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=s_fields, extrasaction='ignore')
    w.writeheader()
    for r in spatial_rows:
        w.writerow({k: (fmt(r[k]) if isinstance(r.get(k), float) else r.get(k, "")) for k in s_fields})
        
# CSV Output Temporal
t_csv = cp.TABLES_DIR / f"temporal_metrics_{YEAR}.csv"
t_fields = ["variable", "reference", "period", "n_valid", "MB", "MAE", "RMSE", "r", "KGE"]
with open(t_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=t_fields, extrasaction='ignore')
    w.writeheader()
    for r in temporal_rows:
        w.writerow({k: (fmt(r[k]) if isinstance(r.get(k), float) else r.get(k, "")) for k in t_fields})

print(f"  ✔ Spatial CSV → {s_csv.name}")
print(f"  ✔ Temporal CSV → {t_csv.name}")
